# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Virtual API class """
# -------------------------------------------------------
# Nadège LEMPERIERE, @16th September 2024
# Latest revision: 16th September 2024
# -------------------------------------------------------

#pylint: disable=W0107, W0613
class API:
    """ Virtual API class """

    def __init__(self):
        """ Constructor"""

    def login(self, credentials):
        """
        Login to the API
        Parameters    :
            credentials (dict) : The credentials to use for the login
        Returns       : Nothing
        Throws        : Exception if the token acquisition fails
        """
        pass

    def mock(self, functions) :
        """
        Mock Microsoft API Data With Synthetic Ones
        Parameters    :
            functions (dict) : The get and post functions to use instead of requests ones
        Throws        : Exception if the token acquisition fails or credentials are invalid
        """
        pass

    def get_user(self) :
        """
        Retrieve the authorized user information
        Returns (dict) : The authorized user information
        Throws         : Exception if the user info retrieval fails
        """
        return {}

    def get_contacts(self):
        """
        Retrieve all the user contacts
        Returns (array) : The list of all contacts
        Throws          : Exception if the calendar list retrieval fails
        """
        return []

    def get_calendars(self):
        """
        Retrieve all the calendars of the authorized user
        Returns (array) : The list of all contacts
        Throws          : Exception if the calendar list retrieval fails
        """
        return []

    def get_events(self, identifier, days):
        """
        Retrieve all events from a calendar
        Parameters      :
            identifier (str) : Identifier of the calendar to search
            days (int)       : Number of days to search for from now
        Returns (array) : list of the calendar events
        Throws          : Exception if the retrieval fails
        """
        return []


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
        return {}

    def post_custom_properties(self, identifier, name, data, calendar=None):
        """
        Update the custom properties of an event
        Parameters     :
            calendar(str)    : Identifier of the calendar containing the event
            identifier (str) : Identifier of the event to update
            data (dict)      : Data to use as custom properties
        Throws         : Exception if the update fails
        """
        pass


    def post_mail(self, subject, content, recipient) :
        """
        Send an email using the Microsoft Graph API and the authorized user email*
        Parameters     :
            subject (str)   : Subject of the email
            content (str)   : Content of the email
            recipient (str) : Address of the email recipient
        Throws         : Exception if the sending fails
        """
        pass
#pylint: enable=W0107, W0613
