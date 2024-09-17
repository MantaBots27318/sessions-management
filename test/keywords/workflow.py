# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Registration workflow keywords """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# System includes
from sys       import path as relpath
from os        import path
from json      import load
from datetime  import datetime, timedelta, timezone
from zoneinfo  import ZoneInfo
from logging   import config, getLogger
from copy      import deepcopy
relpath.append(path.relpath("../../"))

# Robotframework includes
from robot.libraries.BuiltIn import BuiltIn, _Misc
from robot.api               import logger as logger
from robot.api.deco          import keyword
ROBOT = False

# Project includes
from manager                 import Registration

# Local includes
from microsoft               import MicrosoftMockAPI
from smtpmock                import MockSMTPServer
from imapmock                import MockImapServer
from parser                  import Parser
from comparer                import Comparer

# Logger configuration settings
logg_conf_path = path.normpath(path.join(path.dirname(__file__), '../../conf/logging.conf'))

now = datetime.now(timezone.utc)

@keyword('Load Scenario Data')
def load_scenario_data(identifier, conf) :
    """ Load test data and test configuration"""

    result = {}

    # Load scenario data
    result = Parser.read_scenario(identifier, conf)

    # Format events timestamp info into datetime objects
    for event in result['data']['events'] :

        event['start'] = {}
        event['end'] = {}
        start = now.astimezone(result['timezone']) + timedelta(hours=event['delta_start_hours'])
        end = now.astimezone(result['timezone']) + timedelta(hours=event['delta_end_hours'])

        # If event lasts one or more full days, set its start time to 00:00:00
        # and its end time to 00:00:00 of the next day. Remove one second to
        # handle the case where the event already ends at 00:00:00 of the next day.
        if event['full_day'] == 'true':
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = end + timedelta(seconds=-1)
            end = end.replace(hour=0, minute=0, second=0, microsecond=0)

        event['start']['date'] = start
        event['end']['date'] = end

    return result


@keyword('Load Results')
def load_results(identifier, conf) :
    """ Load test results """

    result = {}

    # Load scenario data
    result = Parser.read_results(identifier, conf)

    return result

@keyword('Run Registration Workflow with Mocks')
def run_registration_workflow_with_mocks(scenario, receiver, sender) :

    result = {
        'microsoft' : MicrosoftMockAPI(scenario['data']),
        'smtp' : MockSMTPServer(scenario['data']['smtp']),
        'imap' : MockImapServer(scenario['data']['imap'])
    }

    config.fileConfig(logg_conf_path)

    registration = Registration(
        'token.json', mail='smtp_password',
        getfunc = result['microsoft'].get,
        postfunc = result['microsoft'].post,
        smtp_server=result['smtp'],
        imap_server=result['imap'])

    registration.configure(scenario['conf'], receiver, sender)
    registration.search_events()
    registration.prepare_emails()
    registration.send_emails()

    return result

@keyword('Check Final State')
def check_final_state(reference, results) :


    mails = results['smtp'].get_mails()
    events = results['microsoft'].scenario()['events']

    Comparer.compare_emails_number(reference,results)

    for mail in mails :

        logger.debug(mail['subject'])

        # Get associated event id
        event_id = mail['subject'][\
            mail['subject'].find('[') + 1:\
            mail['subject'].find(']')]

        # Get associated event
        associated_event = {}
        found = False
        for event in events :
            if event['id'] == event_id :
                found = True
                associated_event = event

        if not found : raise Exception('Event id ' + event_id + ' not found')
        logger.debug(f'Event {event_id} found')

        found = False
        for test in reference['data']['mails'] :

            reference_id = test['subject'][\
                test['subject'].find('[') + 1:\
                test['subject'].find(']')]

            if reference_id == event_id :
                found = True
                actual = {'mail' : mail, 'event' : associated_event}

                Comparer.compare_email(
                    test, actual, reference['timezone'], reference['data']['full'])
                Comparer.compare_registration(
                    test, actual, reference['timezone'], reference['data']['full'])

        if not found : raise Exception('Event id ' + event_id + ' not found')

@keyword('Update Scenario Data From Results')
def update_scenario_data_from_results(scenario, results) :

    scenario['data']['events'] = results['microsoft'].scenario()['events']
    logger.debug(scenario)

    return scenario

@keyword('Merge Scenario Data')
def merge_scenario_data(scenario, scenario2) :

    result = deepcopy(scenario)

    for data2 in scenario2['data']['events'] :
        found = False
        for data in result['data']['events'] :
            if data['id'] == data2['id'] :
                found = True
                data['start'] = data2['start']
                data['end'] = data2['end']
                data['full_day'] = data2['full_day']
                data['delta_start_hours'] = data2['delta_start_hours']
                data['delta_end_hours'] = data2['delta_end_hours']
                data['attendees'] = data2['attendees']

        if not found : result['data']['events'].append(data2)

    for data2 in scenario2['data']['contacts'] :
        found = False
        for data in result['data']['contacts'] :
            if data['mail'] == data2['mail'] :
                found = True
                data = deepcopy(data2)

        if not found : result['data']['contacts'].append(data2)

    return result