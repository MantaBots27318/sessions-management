# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Google API mock for testing """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# System includes
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from json import dumps, loads
from requests import Response
from copy import deepcopy

class MicrosoftAPI:
    """ A mock class to simulate requests to microsoft API """

    s_TestCalendar = "Test Calendar"

    def __init__(self, scenario):
        self.__scenario = deepcopy(scenario)

    def get(self, endpoint, headers={}, params={}) :

        response = MockMicrosoftResponse()
        if endpoint == 'https://graph.microsoft.com/v1.0/me' :
            response.status_code  = 200
            response.set_content({"mail":"me@me.org"})

        elif endpoint == 'https://graph.microsoft.com/v1.0/me/contacts' :
            try :
                response.set_content({'value' : self.__format_contacts()})
                response.status_code  = 200
            except Exception as e :
                response.status_code  = 404
                response.set_content({'error' : str(e)})

        elif endpoint == 'https://graph.microsoft.com/v1.0/me/calendars' :
            response.status_code  = 200
            response.set_content({'value' : self.__scenario['calendars'] })

        elif endpoint.startswith('https://graph.microsoft.com/v1.0/me/calendars/') :
            try :
                id = endpoint.split('/')[-2]
                response.set_content({
                    'value' : self.__format_events(id, params['startDateTime'],params['endDateTime'])
                })
                response.status_code  = 200
            except Exception as e :
                response.status_code  = 404
                response.set_content({'error' : str(e)})

        elif endpoint.startswith('https://graph.microsoft.com/v1.0/me/events/')  :
            try :
                id = endpoint.split('/')[-3]
                extension = endpoint.split('/')[-1]
                response.set_content(
                    self.__format_extensions(id, extension))
                response.status_code  = 200
            except Exception as e :
                response.status_code  = 404
                response.set_content({'error' : str(e)})

        return response

    def post(self, endpoint, headers={}, params={}, data={}, json={}) :

        response = MockMicrosoftResponse()
        if endpoint.startswith('https://graph.microsoft.com/v1.0/me/events/') and \
             endpoint.find('/extensions') > 0 :
            try :
                self.__update_extensions(endpoint.split('/')[-2], json)
                response.status_code  = 201
            except Exception as e :
                response.status_code  = 404
                response.set_content({'error' : str(e)})

        elif endpoint.startswith('https://login.microsoftonline.com/common/oauth2/v2.0/token') :
            response.status_code  = 200
            response.set_content({'access_token' : ''})

        return response

    def __format_events(self, identifier, timeMin, timeMax):

        result = []

        # Check that the required calendar exists
        found = False
        for calendar in self.__scenario['calendars'] :
            if calendar['id'] == identifier :
                found = True
                calendar = calendar
        if not found : raise Exception('Calendar %s not found', id)

        # If the calendar is the Test Calendar, list its events from the scenario data

        if calendar['name'] == MicrosoftAPI.s_TestCalendar :
            for event in self.__scenario['events'] :
                item = {}

                # Format the event into Microsoft Graph API format
                item['isCancelled'] = not(event['status'] == 'confirmed')
                item['subject'] = event['summary']
                item['id'] = event['id']

                if event['full_day'] == 'true': item['isAllDay'] = True
                else : item['isAllDay'] = False

                item['attendees'] = []
                for attendee in event['attendees'] :
                    item['attendees'].append({
                        'emailAddress' :  {'address':  attendee['mail']}
                    })

                utc = ZoneInfo('UTC')
                item['start'] = {}
                item['end'] = {}
                start = event['start']['date'].astimezone(utc)
                end = event['end']['date'].astimezone(utc)
                item['start']['dateTime'] = start.strftime('%Y-%m-%dT%H:%M:%S.%f') + '0'
                item['end']['dateTime'] = end.strftime('%Y-%m-%dT%H:%M:%S.%f') + '0'
                item['start']['timeZone'] = 'UTC'
                item['end']['timeZone'] = 'UTC'

                if end.timestamp()  >= datetime.fromisoformat(timeMin).timestamp()  and \
                   start.timestamp()  < datetime.fromisoformat(timeMax).timestamp()  :
                    if event['full_day'] == 'true':
                        # Mock the error microsoft does on full event, not taking into account the creation timezone
                        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
                        end = end.replace(hour=0, minute=0, second=0, microsecond=0)
                        item['start']['dateTime'] = start.strftime('%Y-%m-%dT%H:%M:%S.%f') + '0'
                        item['end']['dateTime'] = end.strftime('%Y-%m-%dT%H:%M:%S.%f') + '0'
                    result.append(item)

        return result

    def __format_contacts(self):

        result = []

        for contact in self.__scenario['contacts'] :
            item = {}
            item['jobTitle'] = contact['role']
            item['emailAddresses'] = [{'address' : contact['mail']}]
            item['displayName'] = contact['name']
            result.append(item)

        return result

    def __format_extensions(self, identifier, extension):

        result = {}
        found = False

        if extension == 'org.mantabots' :
            for event in self.__scenario['events'] :
                if event['id'] == identifier :
                    found = True
                    if 'registration' in event :
                        result = event['registration']

        if not found :
            raise Exception('Event %s not found', id)

        return result

    def __update_extensions(self, identifier, data):

        if 'extensionName' in data and data['extensionName'] == 'org.mantabots' :
            found = False
            for event in self.__scenario['events'] :
                if event['id'] == identifier :
                    found = True
                    event['registration'] = data

            if not found :
                raise Exception('Event %s not found', id)
        else :
            raise Exception('Extension org.mantabots not found')

    def scenario(self) :
        return self.__scenario

class MockMicrosoftResponse:

    def __init__(self):
        self.content = ''
        self.text = ''
        self.status_code = 0

    def json(self):
        return loads(self.content.decode('utf-8'))

    def set_content(self, value) :
        self.content = dumps(value).encode('utf-8')
        self.text = dumps(value)