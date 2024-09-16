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
relpath.append(path.relpath("../../"))

# Robotframework includes
from robot.libraries.BuiltIn import BuiltIn, _Misc
from robot.api               import logger as logger
from robot.api.deco          import keyword
ROBOT = False

# Project includes
from manager                 import Registration

# Local includes
from microsoft               import MicrosoftAPI
from smtpmock                import MockSMTPServer
from imapmock                import MockImapServer
from tools                   import Tools


# Scenarii configuration settings
scenarii_path = path.normpath(path.join(path.dirname(__file__), '../data/scenarii.json'))

# Results data
results_path = path.normpath(path.join(path.dirname(__file__), '../data/results.json'))

# Input data
data_path = path.normpath(path.join(path.dirname(__file__), '../data/data.json'))

# Logger configuration settings
logg_conf_path = path.normpath(path.join(path.dirname(__file__), '../../conf/logging.conf'))


@keyword('Build Scenario Data')
def build_scenario_data(scenario) :

    result = {}

    # Load scenario data
    with open(scenarii_path, encoding="utf-8") as file: scenarii = load(file)
    # Load input data
    with open(data_path, encoding="utf-8") as file: data = load(file)
    # Load scenario results
    with open(results_path, encoding="utf-8") as file: results = load(file)

    if not scenario in scenarii : raise Exception('Scenario not found')
    if not scenario in results : raise Exception('Scenario not found')

    result['data'] = data[scenarii[scenario]['data']]
    result['conf'] = scenarii[scenario]['conf']
    result['results'] = results[scenario]

    # Read timezone from configuration file
    app_conf_path = path.normpath(path.join(path.dirname(__file__), '../../', result['conf']))
    result['timezone'] = Tools.read_timezone(app_conf_path)

    # Format events timestamp info into datetime objects
    for event in result['data']['events'] :

        event['start'] = {}
        event['end'] = {}
        start = datetime.now(result['timezone']) + timedelta(hours=event['delta_start_hours'])
        end = datetime.now(result['timezone']) + timedelta(hours=event['delta_end_hours'])

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

@keyword('Run Registration Workflow with Mocks')
def run_registration_workflow_with_mocks(scenario, receiver, sender) :

    result = {
        'microsoft' : MicrosoftAPI(scenario['data']),
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
def check_final_state(scenario, results) :

    mails = results['smtp'].get_mails()
    events = results['microsoft'].scenario()['events']

    if len(mails) != len(scenario['results']['mails']) :
        raise Exception('Different number of emails sent')

    for mail in mails :

        mail_found = False
        for test in scenario['results']['mails'] :

            # Get associated event id
            event_id = mail['subject'][\
                mail['subject'].find('[') + 1:\
                mail['subject'].find(']')]

            found = False
            local_test = {'subject' : '', 'content' : ''}
            for event in events :
                if event['id'] == event_id :
                    found = True

                    tz = ZoneInfo('UTC')
                    start_date = event['start']['date']
                    end_date = event['end']['date']
                    if event['full_day'] == 'true' : end_date = end_date + timedelta(seconds=-1)
                    elif scenario['results']['full'] == 'true' and event['full_day'] != 'true':
                        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        end_date = end_date + timedelta(seconds=-1)
                        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
                    start_date = start_date.astimezone(tz)
                    end_date = end_date.astimezone(tz)
                    start_date_utc   = start_date.strftime('%Y-%m-%dT%H:%M:%S%z')
                    end_date_utc     = end_date.strftime('%Y-%m-%dT%H:%M:%S%z')
                    start_date_local = start_date.astimezone(scenario['timezone'])
                    end_date_local   = end_date.astimezone(scenario['timezone'])

                    local_test['subject'] = test['subject'].replace('{{start_date}}',start_date_local.strftime('%A, %d. %B %Y'))
                    local_test['subject'] = local_test['subject'].replace('{{end_date}}',end_date_local.strftime('%A, %d. %B %Y'))
                    local_test['content'] = test['content'].replace('{{start_date}}',start_date_local.strftime('%A, %d. %B %Y'))
                    local_test['content'] = local_test['content'].replace('{{end_date}}',end_date_local.strftime('%A, %d. %B %Y'))

                    local_test['subject'] = local_test['subject'].replace('{{start_time}}',start_date_local.strftime('%I:%M%p'))
                    local_test['subject'] = local_test['subject'].replace('{{end_time}}',end_date_local.strftime('%I:%M%p'))
                    local_test['content'] = local_test['content'].replace('{{start_time}}',start_date_local.strftime('%I:%M%p'))
                    local_test['content'] = local_test['content'].replace('{{end_time}}',end_date_local.strftime('%I:%M%p'))

                    logger.debug(event)

                    if not 'registration' in event : raise Exception('Event not updated after email sent')
                    if not 'sent' in event['registration'] : raise Exception('Event not updated after email sent')
                    if not 'start' in event['registration'] : raise Exception('Event not updated after email sent')
                    if not 'end' in event['registration'] : raise Exception('Event not updated after email sent')
                    if not 'students' in event['registration'] : raise Exception('Event not updated after email sent')
                    if not 'coaches' in event['registration'] : raise Exception('Event not updated after email sent')

                    if not event['registration']['sent'] : raise Exception('Event sent status is not true')
                    if event['registration']['start'] != start_date_utc : raise Exception('Start date does not match email')
                    if event['registration']['end'] != end_date_utc : raise Exception('End date does not match email')


            if not found : raise Exception('Event id ' + event_id + ' not found')

            if test['from'] == mail['from'] and \
               test['to'] == mail['to'] and \
               local_test['subject'] == mail['subject'] and \
               local_test['content'] == mail['content'] :
               mail_found = True

        if not mail_found : raise Exception('No matching email found')

@keyword('Update Scenario Data From Results')
def update_scenario_data_from_results(scenario, results) :

    scenario['data']['events'] = results['microsoft'].scenario()['events']

    return scenario

@keyword('Merge Scenario Data')
def merge_scenario_data(scenario, scenario2) :

    for i_data, data in enumerate(scenario2['data']['events']) :
        found = False
        for data2 in scenario['data']['events'] :
            if data2['id'] == data['id'] :
                found = True
                scenario['data']['events'][i_data]['start'] = data['start']
                scenario['data']['events'][i_data]['end'] = data['end']
                scenario['data']['events'][i_data]['delta_start_hours'] = data['delta_start_hours']
                scenario['data']['events'][i_data]['delta_end_hours'] = data['delta_end_hours']
                scenario['data']['events'][i_data]['attendees'] = data['attendees']

        if not found : scenario['data']['events'].append(data)

    scenario['results'] = scenario2['results']

    return scenario