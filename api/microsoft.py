# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Microsoft API class """
# -------------------------------------------------------
# Nadège LEMPERIERE, @16th September 2024
# Latest revision: 17th September 2024
# -------------------------------------------------------

# System includes
from logging  import getLogger
from os       import path
from json     import load, loads
from datetime import datetime, timedelta, timezone
from copy     import deepcopy

# Requests includes
from requests import get, post

# Local includes
from api.api  import API


#pylint: disable=W0719, R0902
class MicrosoftAPI(API):
    """ Microsoft Graph API class """

    def __init__(self):
        """ Constructor"""

        super().__init__()

        # Initialize logger
        self.__logger = getLogger('microsoft')
        self.__logger.info('--> Using Microsoft Graph API')

        # Initialize members
        self.__token = ""
        self.__get  = get
        self.__post = post

    def mock(self, functions) :
        """
        Mock Microsoft API Data With Synthetic Ones
        Parameters    :
            functions (dict) : The get and post functions to use instead of requests ones
        Throws        : Exception if the token acquisition fails or credentials are invalid
        """

        self.__logger.info("---> Mocking Microsoft data with synthetic ones")

        if 'get' in functions  : self.__get = functions['get']
        if 'post' in functions : self.__post = functions['post']

    def login(self, credentials):
        """
        Login to the API
        Parameters    :
            credentials (str) : The credentials file to use for the login
        Throws        : Exception if the token acquisition fails or credentials are invalid
        """

        self.__logger.info("---> Login to Microsoft Graph API")

        credentials_path = path.normpath(path.join(path.dirname(__file__),'../', credentials))
        with open(credentials_path, encoding="utf-8") as file:
            data = load(file)

        if not 'client_id'     in data : raise Exception("Invalid credentials")
        if not 'client_secret' in data : raise Exception("Invalid credentials")
        if not 'refresh_token' in data : raise Exception("Invalid credentials")
        if not 'scopes'        in data : raise Exception("Invalid credentials")

        # Data payload for the token request
        data = {
            'client_id': data['client_id'],
            'client_secret': data['client_secret'],
            'refresh_token': data['refresh_token'],
            'grant_type': 'refresh_token',
            'redirect_uri': 'https://mantabots.org',
            'scope': data['scopes']
        }

        # Make the POST request to acquire a new access token using the refresh token
        # USING THE COMMON ENDPOINT TO ACCESS PERSONAL ACCOUNTS IS KEY
        endpoint = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        response = self.__post(endpoint, data=data)

        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Error acquiring token: {response.text}")

        # Parse the JSON response
        token_response = response.json()

        # Acquire an access token
        if "access_token" not in token_response:
            raise Exception(f"Error acquiring token: {token_response.get('error_description')}")

        # Store the access token
        self.__token = token_response['access_token']

        self.__logger.info("---> Logged in Microsoft Graph API")

    def get_user(self) :
        """
        Retrieve the authorized user information
        Returns (dict) : The authorized user information
        Throws         : Exception if the user info retrieval fails
        """

        result = {}

        self.__logger.info("---> Retrieving authorized user info")

        # Define the endpoint and headers for the authorized user request
        endpoint = "https://graph.microsoft.com/v1.0/me"
        headers = { 'Authorization': f'Bearer {self.__token}','Content-Type': 'application/json'}

        # Send the request to get user
        response = self.__get(endpoint, headers=headers)
        if response.status_code == 200: result = response.json()
        else : raise Exception(f"Failed retrieving user with error : {response.text}")

        self.__logger.info("---> Found authorized user info")

        return result

    def get_contacts(self):
        """
        Retrieve all the contacts of the authorized user
        Returns (array) : The list of all contacts
        Throws          : Exception if the calendar list retrieval fails
        """

        result = []

        self.__logger.info("---> Retrieving contacts")

        # Define the endpoint and headers for the contacts request
        endpoint = "https://graph.microsoft.com/v1.0/me/contacts"
        headers = { 'Authorization': f'Bearer {self.__token}', 'Content-Type': 'application/json' }

        # Send the request to get contacts
        response = self.__get(endpoint, headers=headers,
            params={'$top': 25, '$select': 'displayName,emailAddresses,jobTitle,categories'})
        if response.status_code == 200: result = response.json().get('value', [])
        else : raise Exception(f"Failed retrieving contacts with error : {response.content}")

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

        # Define the endpoint and headers for the calendars request
        endpoint = "https://graph.microsoft.com/v1.0/me/calendars"
        headers = { 'Authorization': f'Bearer {self.__token}', 'Content-Type': 'application/json'}

        # Send the request to get calendars
        response = self.__get(endpoint, headers=headers)
        if response.status_code == 200: result = response.json().get('value', [])
        else : raise Exception(f"Failed retrieving calendars list with error : {response.content}")

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

        # Define the endpoint and headers for the events request
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendars/{identifier}/calendarview"
        headers = { 'Authorization': f'Bearer {self.__token}', 'Content-Type': 'application/json'}

        # Define the parameters for the events request
        now = datetime.now(timezone.utc)
        params = {
            'startDateTime': now.isoformat(timespec='seconds'),
            'endDateTime': (now + timedelta(days=days)).isoformat(timespec='seconds'),
            '$orderby': 'start/dateTime',
            '$top': 10
        }

        # Send the request to get calendar events
        response = self.__get(endpoint, headers=headers, params=params)
        if response.status_code == 200: result = response.json().get('value', [])
        else : raise Exception(f"Failed retrieving events with error : {response.content}")

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

        # Define the endpoint and headers for the properties retrieval
        headers = { 'Authorization': f'Bearer {self.__token}', 'Content-Type': 'application/json'}
        endpoint = f"https://graph.microsoft.com/v1.0/me/events/{identifier}/extensions/{name}"
        response = self.__get(endpoint, headers=headers, params={})

        # Get the custom properties
        print(response.content)
        if response.status_code == 200: result = loads(response.content.decode('utf-8'))

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

        # Define the endpoint and headers for the properties posting
        headers = { 'Authorization': f'Bearer {self.__token}', 'Content-Type': 'application/json'}
        endpoint = f"https://graph.microsoft.com/v1.0/me/events/{identifier}/extensions"

        # Format data
        local_data = deepcopy(data)
        local_data["@odata.type"] = "microsoft.graph.openTypeExtension"
        local_data["extensionName"] = name

        # Post the custom properties
        response = self.__post(endpoint, headers=headers, json=local_data)
        if response.status_code != 201:

            raise Exception(f"Failed to update extensions with error : {response.text}")

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

        # Define the endpoint and headers for the properties retrieval
        endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
        headers = { 'Authorization': f'Bearer {self.__token}', 'Content-Type': 'application/json'}

        # Format email message
        email_message = {
            "message": {
                "subject": subject,
                "body": { "contentType": "Text", "content": content },
                "toRecipients": [
                    { "emailAddress": { "address": recipient  } }
                ]
            },
            "saveToSentItems": "true"
        }

        # Send email
        response  = self.__post(endpoint, headers=headers, json=email_message)
        if response.status_code != 202: raise Exception(f"Failed to send email : {response.text}")

        self.__logger.info("---> Mail sent")
#pylint: enable=W0719, R0902
