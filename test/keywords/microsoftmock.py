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

class MockMicrosoftLibrary:
    """ A mock class to simulate requests to microsoft API """

    def __init__(self, scenario):
        self.__scenario = deepcopy(scenario)
        self.__services = {}

    def get(self, endpoint, headers={}, params={}) :

        print(endpoint)

        response = MockMicrosoftResponse()
        if endpoint == 'https://graph.microsoft.com/v1.0/me' :
            response.status_code  = 200
            response.set_content({"mail":"me@me.org"})

        elif endpoint == 'https://graph.microsoft.com/v1.0/me/contacts' :
            try :
                response.set_content({'value' : self.__list_contacts()})
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
                    'value' : self.__list_events(id, params['startDateTime'],params['endDateTime'])
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
                    self.__list_extensions(id, extension))
                response.status_code  = 200
            except Exception as e :
                response.status_code  = 404
                response.set_content({'error' : str(e)})

        return response

    def post(self, endpoint, headers={}, params={}, data={}, json={}) :

        response = MockMicrosoftResponse()
        print(endpoint)
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

    def __list_events(self, id, timeMin, timeMax):

        result = []

        found = False
        for calendar in self.__scenario['calendars'] :
            if calendar['id'] == id :
                found = True
                calendar = calendar

        if not found : raise Exception('Calendar %s not found', id)

        if calendar['name'] == 'Test Calendar' :
            for item in self.__scenario['items'] :
                temp = deepcopy(item)
                temp['isCancelled'] = not(temp['status'] == 'confirmed')
                temp['subject'] = temp['summary']

                for i_attendee, attendee in enumerate(temp['attendees']) :
                    temp['attendees'][i_attendee]['emailAddress'] = {
                        'address':  temp['attendees'][i_attendee]['email']
                    }

                if temp['full_day'] == 'true': temp['isAllDay'] = True
                else : temp['isAllDay'] = False

                timezone = ZoneInfo('UTC')
                start = temp['start']['date'].astimezone(timezone)
                end = temp['end']['date'].astimezone(timezone)
                temp['start']['dateTime'] = start.strftime('%Y-%m-%dT%H:%M:%S.%f') + '0'
                temp['end']['dateTime'] = end.strftime('%Y-%m-%dT%H:%M:%S.%f') + '0'
                temp['start']['timeZone'] = 'UTC'
                temp['end']['timeZone'] = 'UTC'
                del temp['start']['date']
                del temp['end']['date']

                if end.timestamp()  >= datetime.fromisoformat(timeMin).timestamp()  and \
                start.timestamp()  < datetime.fromisoformat(timeMax).timestamp()  :
                    result.append(temp)

        return result

    def __list_contacts(self):

        result = []

        for item in self.__scenario['connections'] :
            temp = deepcopy(item)
            temp['jobTitle'] = temp['organizations'][0]['title']
            for i_address,address in enumerate(item['emailAddresses']) :
                temp['emailAddresses'][i_address]['address'] = \
                    temp['emailAddresses'][i_address]['value']
            if 'names' in temp :
                temp['displayName'] = temp['names'][0]['displayName']
            result.append(temp)

        return result

    def __list_extensions(self, id, extension):

        result = {}
        found = False

        if extension == 'org.mantabots' :
            for item in self.__scenario['items'] :
                temp = deepcopy(item)
                if temp['id'] == id :
                    found = True
                    if 'extendedProperties' in temp and 'private' in temp['extendedProperties'] :
                        result = temp['extendedProperties']['private']

        if not found :
            raise Exception('Event %s not found', id)

        return result

    def __update_extensions(self, id, data):


        if 'extensionName' in data and data['extensionName'] == 'org.mantabots' :
            found = False
            for i_item, item in enumerate(self.__scenario['items']) :
                if item['id'] == id :
                    found = True
                    self.__scenario['items'][i_item]['extendedProperties'] = {'private' : data}

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