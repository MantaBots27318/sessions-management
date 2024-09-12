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
from googlemock              import MockGoogleLibrary
from smtpmock                import MockSMTPServer


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
    with open(scenarii_path, encoding="utf-8") as file:
        scenarii = load(file)
    # Load input data
    with open(data_path, encoding="utf-8") as file:
        data = load(file)
    # Load scenario results
    with open(results_path, encoding="utf-8") as file:
        results = load(file)

    if not scenario in scenarii : raise Exception('Scenario not found')
    if not scenario in results : raise Exception('Scenario not found')

    result['data'] = data[scenarii[scenario]['data']]
    result['conf'] = scenarii[scenario]['conf']
    result['results'] = results[scenario]

    # Format datetime data
    for i_item, item in enumerate(result['data']['google']['items']) :
        
        result['data']['google']['items'][i_item]['start'] = {}
        result['data']['google']['items'][i_item]['end'] = {}
        
        if result['data']['google']['items'][i_item]['full_day'] == 'true':
            result['data']['google']['items'][i_item]['start']['date'] = \
                (datetime.now(timezone.utc) + timedelta(hours=item['delta_start_hours'])).strftime('%Y-%m-%d')
            result['data']['google']['items'][i_item]['end']['date'] = \
                (datetime.now(timezone.utc) + timedelta(hours=item['delta_end_hours'])).strftime('%Y-%m-%d')

        else :
            result['data']['google']['items'][i_item]['start']['dateTime'] = \
                (datetime.now(timezone.utc) + timedelta(hours=item['delta_start_hours'])).strftime('%Y-%m-%dT%H:%M:%S%z')
            result['data']['google']['items'][i_item]['end']['dateTime'] = \
                (datetime.now(timezone.utc) + timedelta(hours=item['delta_end_hours'])).strftime('%Y-%m-%dT%H:%M:%S%z')

    return result

@keyword('Run Registration Workflow with Mocks')
def run_registration_workflow_with_mocks(scenario, receiver, sender) :
    
    result = {
        'google' : MockGoogleLibrary(scenario['data']['google']),
        'smtp' : MockSMTPServer(scenario['data']['smtp'])
    }

    config.fileConfig(logg_conf_path)

    registration = Registration(
        'token.json', smtp='smtp_password', 
        google_service=result['google'], 
        smtp_server=result['smtp'])

    registration.configure(scenario['conf'], receiver, sender)
    registration.search_events()
    registration.get_attendees()
    registration.prepare_emails()
    registration.send_emails()

    return result

@keyword('Check Final State')
def check_final_state(scenario, results) :


    mails = results['smtp'].get_mails()
    events = results['google'].get('calendar').scenario()['items']

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

                    start_date = datetime.now(timezone.utc) + timedelta(hours=event['delta_start_hours'])
                    end_date = datetime.now(timezone.utc) + timedelta(hours=event['delta_end_hours'])

                    if 'date' in event['start']:
                        start_date_string = start_date.strftime('%A, %d. %B %Y') + " at 12:00AM"
                        end_date_string = end_date.strftime('%A, %d. %B %Y') + " at 12:00AM"
                    elif scenario['results']['full'] != 'true' and 'dateTime' in event['start']: 
                        start_date_string = start_date.strftime('%A, %d. %B %Y') + " at " + start_date.strftime('%I:%M%p')
                        end_date_string = end_date.strftime('%A, %d. %B %Y') + " at " + end_date.strftime('%I:%M%p') 
                    elif scenario['results']['full'] == 'true' and 'dateTime' in event['start']:
                        start_date_string = start_date.strftime('%A, %d. %B %Y') + " at 12:00AM"
                        end_date_string = end_date.strftime('%A, %d. %B %Y') + " at 11:59PM"
                    else :
                        start_date_string = ""
                        end_date_string = ""

                
                    local_test['subject'] = test['subject'].replace('{{start_date}}',start_date.strftime('%A, %d. %B %Y'))
                    local_test['subject'] = local_test['subject'].replace('{{end_date}}',end_date.strftime('%A, %d. %B %Y'))
                    local_test['content'] = test['content'].replace('{{start_date}}',start_date.strftime('%A, %d. %B %Y'))
                    local_test['content'] = local_test['content'].replace('{{end_date}}',end_date.strftime('%A, %d. %B %Y'))
                    
                    local_test['subject'] = local_test['subject'].replace('{{start_time}}',start_date.strftime('%I:%M%p'))
                    local_test['subject'] = local_test['subject'].replace('{{end_time}}',end_date.strftime('%I:%M%p'))
                    local_test['content'] = local_test['content'].replace('{{start_time}}',start_date.strftime('%I:%M%p'))
                    local_test['content'] = local_test['content'].replace('{{end_time}}',end_date.strftime('%I:%M%p'))

                    if not 'extendedProperties' in event : raise Exception('Event not updated after email sent')
                    if not 'private' in event['extendedProperties'] : raise Exception('Event not updated after email sent')
                    if not 'sent' in event['extendedProperties']['private'] : raise Exception('Event not updated after email sent')
                    if not 'start' in event['extendedProperties']['private'] : raise Exception('Event not updated after email sent')
                    if not 'end' in event['extendedProperties']['private'] : raise Exception('Event not updated after email sent')
                    if not event['extendedProperties']['private']['sent'] : raise Exception('Event sent status is not true')
                    if event['extendedProperties']['private']['start'] != start_date_string : raise Exception('Start date does not match email')
                    if event['extendedProperties']['private']['end'] != end_date_string : raise Exception('End date does not match email')


            if not found : raise Exception('Event id ' + event_id + ' not found')

            if test['from'] == mail['from'] and \
               test['to'] == mail['to'] and \
               local_test['subject'] == mail['subject'] and \
               local_test['content'] == mail['content'] :
               mail_found = True

        if not mail_found : raise Exception('No matching email found')

@keyword('Update Scenario Data From Results')
def update_scenario_data_from_results(scenario, results) :

    scenario['data']['google']['items'] = results['google'].get('calendar').scenario()['items']


    return scenario
    
@keyword('Merge Scenario Data')
def umerge_scenario_data(scenario, scenario2) :

    for i_data, data in enumerate(scenario2['data']['google']['items']) :
        found = False
        for data2 in scenario['data']['google']['items'] :
            if data2['id'] == data['id'] :
                found = True
                scenario['data']['google']['items'][i_data]['start'] = data['start']
                scenario['data']['google']['items'][i_data]['end'] = data['end']
                scenario['data']['google']['items'][i_data]['delta_start_hours'] = data['delta_start_hours']
                scenario['data']['google']['items'][i_data]['delta_end_hours'] = data['delta_end_hours']

        if not found : scenario['data']['google']['items'].append(data)

    scenario['results'] = scenario2['results']

    return scenario