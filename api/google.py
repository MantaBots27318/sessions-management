# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Google API class """
# -------------------------------------------------------
# Nadège LEMPERIERE, @17th September 2024
# Latest revision: 17th September 2024
# -------------------------------------------------------

# System includes
from email.mime.text            import MIMEText

# Google includes
from google.oauth2.credentials  import Credentials
from googleapiclient.discovery  import build

# Local includes
from api.api                    import API

#pylint: disable=W0719, R0902
class GoogleAPI(API):
    """ Google GCP API class """

    s_scopes = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/contacts.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]

    def __init__(self):
        """ Constructor"""

        super().__init__()

        # Initialize logger
        self.__logger = getLogger('google')
        self.__logger.info('USING GOOGLE API')

        self.__token = ""
        self.__build = build

    def mock(self, functions) :
        """
        Mock Google API Data With Synthetic Ones
        Parameters    :
            functions (dict) : The get and post functions to use instead of requests ones
        Throws        : Exception if the token acquisition fails or credentials are invalid
        """

        self.__logger.info("---> Mocking Google data with synthetic ones")

        if 'build' in functions  : self.__build = functions['build']

    def login(self, credentials):
        """
        Login to the API
        Parameters    :
            credentials (str) : The credentials file to use for the login
        Throws        : Exception if the token acquisition fails or credentials are invalid
        """

        self.__logger.info("---> Login to Google API")

        credentials_path = path.normpath(path.join(path.dirname(__file__), credentials))

        self.__token = Credentials.from_authorized_user_file(
            credentials_path, scopes=GoogleAPI.s_scopes
        )

        self.__logger.info("---> Logged in Google API")

    def get_user(self) :
        """
        Retrieve the authorized user information
        Returns (dict) : The authorized user information
        Throws         : Exception if the user info retrieval fails
        """

        result = {}

        self.__logger.info("---> Retrieving authorized user info")

        self.__logger.info("---> Found authorized user info",len(result))

        return result

    def get_contacts(self):
        """
        Retrieve all the contacts of the authorized user
        Returns (array) : The list of all contacts
        Throws          : Exception if the calendar list retrieval fails
        """

        result = []

        self.__logger.info("---> Retrieving contacts")

        # Define the service for the contacts request
        service = self.__build('people', 'v1', credentials=self.__token, cache_discovery=False)
        if not service: raise Exception("Failed to initialize People API service")

        # Send the request to get the contacts
        contacts = service.people().connections().list(
            resourceName='people/me', pageSize=100,
            personFields='names,emailAddresses,organizations,tags'
        ).execute()

        result = contacts.get('connections', [])

        self.__logger.info("---> Found %d contacts",len(result))

        return result

    def get_calendars(self):
        """
        Retrieve all the calendars of the authorized user
        Returns (array) : The list of all contacts
        Throws          : Exception if the calendar list retrieval fails
        """

        result = []

        self.__logger.info("---> Retrieving calendars")

        # Define the service for the calendats request
        service = self.__build('calendar', 'v3', credentials=self.__token, cache_discovery=False)
        if not service: raise Exception("Failed to initialize Calendar API service")

        # Send the request to get the events
        calendars = service.calendars().list().execute()
        result = calendars.get('items', [])

        self.__logger.info("---> Found %d calendars",len(result))

        return result

    def get_events(self, identifier, days):
        """
        Retrieve all events from a calendar
        Parameters      :
            identifier (str) : Identifier of the calendar to search
            days (int)       : Number of days to search for from now
        Returns (array) : list of the calendar events
        Throws          : Exception if the retrieval fails
        """

        result = []
        self.__logger.info("---> Retrieving events")

        # Define the service for the events request
        service = self.__build('calendar', 'v3', credentials=self.__token, cache_discovery=False)
        if not service: raise Exception("Failed to initialize Calendar API service")

        # Define the parameters for the events request
        now = datetime.now(timezone.utc).isoformat()
        end = datetime.now(timezone.utc) + timedelta(days=days).isoformat()

        # Send the request to get the events
        events = service.events().list(
            calendarId=identifier,
            timeMin=now, timeMax=end,
            singleEvents=True, orderBy='startTime'
        ).execute()

        result = events.get('items', [])

        self.__logger.info("---> Found %d events",len(result))

        return result

    def get_custom_properties(self, identifier, name, calendar=None):
        """
        Get the custom properties of an event
        Parameters     :
            calendar(str)    : Identifier of the calendar containing the event
            identifier (str) : Identifier of the event to update
            name (str)       : Extension name to use
        Returns (dict) : Event custom properties (empty if none found)
        Throws         : Exception if the update fails
        """

        result = {}

        self.__logger.info("---> Retrieving custom properties")

        # Define the service for the events request
        service = self.__build('calendar', 'v3', credentials=self.__token, cache_discovery=False)
        if not service: raise Exception("Failed to initialize Calendar API service")

        # Send the request to get the event
        event = service.events().get(
            calendarId=calendar, eventId=identifier
        ).execute()

        # Look for custom properties
        if 'extendedProperties' in event :
            if 'private' in event['extendedProperties'] :
                result = event['extendedProperties']['private']

        self.__logger.info("---> Got custom properties")

        return result

    def post_custom_properties(self, identifier, name, data, calendar=None):
        """
        Update the custom properties of an event
        Parameters     :
            calendar(str)    : Identifier of the calendar containing the event
            identifier (str) : Identifier of the event to update
            data (dict)      : Data to use as custom properties
        Throws         : Exception if the update fails
        """

        self.__logger.info("---> Posting custom properties")

        # Define the service for the events request
        service = self.__build('calendar', 'v3', credentials=self.__token, cache_discovery=False)
        if not service: raise Exception("Failed to initialize Calendar API service")

        # Send the request to get the events
        event = service.events().get(
            calendarId=calendar, eventId=identifier
        ).execute()

        event['extendedProperties'] = { 'private' : data }

        # Send the request to update the event
        event = service.events().update(
            calendarId=calendar, eventId=identifier, body=event
        ).execute()

        self.__logger.info("---> Custom properties posted")


    def post_mail(self, subject, content, recipient) :
        """
        Send an email using the Microsoft Graph API and the authorized user email*
        Parameters     :
            subject (str)   : Subject of the email
            content (str)   : Content of the email
            recipient (str) : Address of the email recipient
        Throws         : Exception if the sending fails
        """

        self.__logger.info("---> Sending email")

        # Define the service for the mail sending
        service = self.__build('gmail', 'v1', credentials=self.__token, cache_discovery=False)
        if not service: raise Exception("Failed to initialize Gmail API service")

        # Format message
        message = MIMEText(content)
        message['subject'] = subject
        message['to'] = recipient
        raw = urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {'raw': raw}

        # Post the request to send the mail
        service.users().messages().send(userId='me', body=message_body).execute()

        self.__logger.info("---> Mail sent")

#pylint: enable=W0719, R0902
