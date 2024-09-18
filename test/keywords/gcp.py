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
from copy import deepcopy

class GoogleMockLibrary:
    """ A mock class to simulate Google python library """

    def __init__(self, scenario):
        """ Initialize API from scenario data"""
        self.__scenario = deepcopy(scenario)
        self.__service = GoogleMockService(self.__scenario)

    def build(self, api, version, credentials, cache_discovery=False):
        """ Mock service building function """
        return self.__service

    def authent(self, filename, scopes) :
        """ Mock credentials acquisition function """
        return ''

    def scenario(self) :
        return self.__scenario

class GoogleMockService:
    """ A mock class to simulate Google API responses """

    def __init__(self, scenario):
        self.__scenario = scenario

    def calendars(self):
        return self

    def events(self):
        return self

    def people(self) :
        return self

    def connections(self) :
        return self

    def calendarList(self) :
        return self

    def contactGroups(self) :
        return self

    def get(self, calendarId = None, resourceName = None, personFields = None, eventId = None) :

        if resourceName is not None and personFields is not None:
            return MockGoogleResponse({
                'emailAddresses': [{'value': "me@me.org"}]
            })
        if resourceName is not None and personFields is None:
            return MockGoogleResponse({
                'formattedName' : resourceName[resourceName.find('/')+1:]
            })
        if calendarId is not None and eventId is None:
            return MockGoogleResponse({
                'summary': 'Test Calendar',
                'description': 'a mock calendar for testing.'
            })
        if calendarId is not None and eventId is not None:
            return self.get_event(calendarId, eventId)


    def list(self, resourceName=None, pageSize=None, personFields=None, calendarId=None, timeMin=None, timeMax=None, singleEvents=None, orderBy=None) :

        if resourceName is not None and pageSize is not None and personFields is not None:
            return self.list_people(resourceName, pageSize, personFields)
        elif calendarId is not None and timeMin is not None and timeMax is not None and singleEvents is not None and orderBy is not None :
            return self.list_events(calendarId, timeMin, timeMax, singleEvents, orderBy)
        else :
            return self.list_calendars()

    def list_calendars(self) :

        result = MockGoogleResponse({
            'items': []
        })

        for calendar in self.__scenario['calendars'] :
            result.data['items'].append({
                'id': calendar['id'],
                'summary': calendar['name']
            })

        return result


    def list_people(self, resourceName, pageSize, personFields) :

        result = MockGoogleResponse({
            'connections': []
        })

        for contact in self.__scenario['contacts'] :
            temp = {
                "organizations" : [{"title" : contact['role']}],
                "emailAddresses" : [{"value" : contact['mail']}],
                "names" : [{"displayName" : contact['name']}],
                'memberships' : []
            }

            for tag in contact['tags'] :
                temp['memberships'].append(
                    {'contactGroupMembership' : {'contactGroupId' : tag}}
                )

            result.data['connections'].append(temp)

        return result

    def list_events(self, calendarId, timeMin, timeMax, singleEvents, orderBy):

        items = []
        for item in self.__scenario['events'] :

            local = {}
            local['id'] = item['id']
            local['status'] = item['status']
            local['summary'] = item['summary']
            local['isAllDay'] = item['full_day'].lower() == 'true'
            local['attendees'] = []
            local['start'] = {}
            local['end'] = {}

            for attendee in item['attendees'] :
                local['attendees'].append({'email' : attendee['mail']})

            if local['isAllDay'] :
                local['start']['date'] = item['start']['date'].strftime('%Y-%m-%d')
                local['end']['date'] = item['end']['date'].strftime('%Y-%m-%d')
            else :
                local['start']['dateTime'] = item['start']['date'].strftime('%Y-%m-%dT%H:%M:%S%z')
                local['end']['dateTime'] = item['end']['date'].strftime('%Y-%m-%dT%H:%M:%S%z')

            if item['end']['date'].timestamp()  >= datetime.fromisoformat(timeMin).timestamp()  and \
               item['start']['date'].timestamp()  < datetime.fromisoformat(timeMax).timestamp()  :
                items.append(local)

        return MockGoogleResponse({
            'items': items
        })

    def get_event(self, calendarId, eventId):

        cid = ''
        registration = {}
        for calendar in self.__scenario['calendars'] :
            if calendar['name'] == 'Test Calendar' :
                cid = calendar['id']

        if calendarId == cid :
            for item in self.__scenario['events'] :
                if item['id'] == eventId :
                    if 'registration' in item :
                        registration = item['registration']

        return MockGoogleResponse(
            {'extendedProperties': { 'private' : registration }}
        )

    def update(self, calendarId, eventId, body):

        found = False
        for item in self.__scenario['events'] :
            if item['id'] == eventId :
                item['registration'] = body['extendedProperties']['private']

        return MockGoogleResponse({'status': 'success'})

    def users(self):
        return self

    def messages(self):
        return self

    def send(self, userId, body):
        return MockResponse({'status': 'sent'})

    def scenario(self) :
        return self.__scenario


class MockGoogleResponse:
    """ A mock response to simulate Google API responses """

    def __init__(self, data):
        self.data = data

    def execute(self):
        return self.data
