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

class MockGoogleLibrary:
    """ A mock class to simulate Google python library """

    def __init__(self, scenario):
        self.__scenario = scenario.copy()
        self.__services = {}

    def build_service(self, api, version, credentials) :
        self.__services[api] = MockGoogleService(api, version, credentials, self.__scenario)
        return self.__services[api]

    def get(self, api) :
        return self.__services[api]

    def scenario(self) :
        return self.__scenario


class MockGoogleService:
    """ A mock class to simulate Google API responses """

    def __init__(self, api, version, credentials, scenario):
        self.__api = api
        self.__version = version
        self.__credentials = credentials
        self.__scenario = scenario.copy()

    def calendars(self):
        return self

    def events(self):
        return self
    
    def people(self) :
        return self

    def connections(self) :
        return self

    def get(self, calendarId):
        return MockResponse({
            'summary': 'Test Calendar',
            'description': 'a mock calendar for testing.'
        })

    def list(self, resourceName=None, pageSize=None, personFields=None, calendarId=None, timeMin=None, timeMax=None, singleEvents=None, orderBy=None) :
        
        if resourceName is not None and pageSize is not None and personFields is not None:
            return self.list_people(resourceName,pageSize,personFields)
        elif calendarId is not None and timeMin is not None and timeMax is not None and singleEvents is not None and orderBy is not None :
            return self.list_events(calendarId, timeMin, timeMax, singleEvents, orderBy)
        else :
            raise Exception("Invalid list parameters set")

    def list_people(self, resourceName, pageSize, personFields) :
        return MockResponse({
            'connections': self.__scenario['connections']
        })

    def list_events(self, calendarId, timeMin, timeMax, singleEvents, orderBy):

        items = []
        for item in self.__scenario['items'] :
            if 'date' in item['start'] :

                start = datetime.strptime(item['start']['date'], '%Y-%m-%d')
                end = datetime.strptime(item['end']['date'], '%Y-%m-%d')

                if end.timestamp()  >= datetime.fromisoformat(timeMin).timestamp()  and \
                   start.timestamp()  < datetime.fromisoformat(timeMax).timestamp()  :
                   items.append(item) 

            elif 'dateTime' in item['start'] :

                start = datetime.strptime(item['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
                end = datetime.strptime(item['end']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')

                if end >= datetime.fromisoformat(timeMin) and \
                   start < datetime.fromisoformat(timeMax) :
                    items.append(item) 

        return MockResponse({
            'items': items
        })

    def update(self, calendarId, eventId, body):

        found = False
        for i_item, item in enumerate(self.__scenario['items']) :
            if item['id'] == eventId :
                self.__scenario['items'][i_item] = body
                if self.__scenario['items'][i_item]['extendedProperties']['private']['sent'] :
                    self.__scenario['items'][i_item]['extendedProperties']['private']['sent'] = 'true'
                else :
                    self.__scenario['items'][i_item]['extendedProperties']['private']['sent'] = 'false'

        return MockResponse({'status': 'success'})

    def users(self):
        return self

    def messages(self):
        return self

    def send(self, userId, body):
        return MockResponse({'status': 'sent'})

    def scenario(self) :
        return self.__scenario


class MockResponse:
    """ A mock response to simulate Google API responses """

    def __init__(self, data):
        self.data = data

    def execute(self):
        return self.data

