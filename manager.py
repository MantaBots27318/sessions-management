# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Session management script """
# -------------------------------------------------------
# Nadège LEMPERIERE, @6th September 2024
# Latest revision: 6th September 2024
# -------------------------------------------------------

# System includes
from logging import config, getLogger
from datetime import datetime, timedelta, timezone
from os import path
from json import load, loads
from time import time
from smtplib import SMTP
from imaplib import IMAP4_SSL, Time2Internaldate
from zoneinfo import ZoneInfo

# Email includes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Click includes
from click import option, group

# Requests includes
from requests import get, post


# Logger configuration settings
logg_conf_path = path.normpath(path.join(path.dirname(__file__), 'conf/logging.conf'))

#pylint: disable=W0719, R0902
class Registration:
    """ Class managing registration workflow """

    # Define scopes for Microsoft Graph API
    s_scopes = [
        'Contacts.Read',
        'Calendars.ReadWrite',
        'Mail.Send'
    ]

#pylint: disable=R0913, C0301
    def __init__(self, microsoft, mail, getfunc=get, postfunc=post, smtp_server=None, imap_server=None):
        """
        Constructor
        Parameters :
            microsoft (str) : Path to the Microsoft Graph API token configuration file
            mail (str)      : Password for the smtp and imap server
            get (function)  : Function to perform GET requests (can be mocked for testing)
            post (function) : Function to perform POST requests (can be mocked for testing)
            smtp_server (str): SMTP object to use for sending emails (can be mocked for testing)
            imap_server (str): IMAP object to use for sending emails (can be mocked for testing)
        Returns    :
        Throws     :
        """
#pylint: enable=C0301

        # Initialize logger
        self.__logger = getLogger('registration')
        self.__logger.info('INITIALIZING REGISTRATION')

        # Mock external API if required
        self.__smtp = smtp_server
        self.__imap = imap_server
        self.__get  = getfunc
        self.__post = postfunc

        # Initialize credentials
        self.__credentials = {}
        token_conf_path = path.normpath(path.join(path.dirname(__file__), microsoft))
        with open(token_conf_path, encoding="utf-8") as file: self.__credentials = load(file)
        self.__mail_password = mail
        self.__conf = {}

        # Authenticate user
        try :
            self.__token = self.__get_token()
            self.__user = self.__get_user(self.__token)
        except Exception as e :
            self.__logger.error('Failed to retrieve authorized user with error %s',str(e))

        # Gather contacts list
        try :
            self.__contacts = self.__initialize_contacts(self.__token)
        except Exception as e :
            self.__logger.error('Failed to retrieve contacts with error %s',str(e))

        # Initialize application data
        self.__events = []

        self.__logger.info('---> Registration initialized')
#pylint: enable=R0913

    def configure(self, conf, receiver, sender):
        """
        Configure the registration workflow from a configuration file and command line parameters
        Parameters :
            conf (str) : Path to the configuration file
            receiver (str)  : Mail recipient address (can be overridden by command line)
            sender (str)  : Mail recipient address (can be overridden by command line)
        Returns    :
        Throws     :
        """

        # Load configuration file
        app_conf_path = path.normpath(path.join(path.dirname(__file__), conf))
        with open(app_conf_path, encoding="utf-8") as file: self.__conf = load(file)

        # Check configuration content and add default values if needed
        if 'team' not in self.__conf :
            self.__conf['team'] = 'MantaBots'

        if 'mail' not in self.__conf :
            self.__conf['mail'] = {}

        if 'from' not in self.__conf['mail'] :
            # Use gmail address through google api
            self.__conf['mail']['from'] = { "address" : "mantabots.infra@outlook.com"}
        if 'address' not in self.__conf['mail']['from'] :
            self.__conf['mail']['from'] = { "address" : "mantabots.infra@outlook.com"}
        # Update configuration from command line parameters
        if len(sender) > 0 : self.__conf['mail']['from']['address'] = sender
        if self.__conf['mail']['from']['address'] != "mantabots.infra@outlook.com" :


            # We need the smtp and imap server configuration
            if len(self.__mail_password) == 0 :
                raise Exception('Missing password for external address')
            self.__conf['mail']['from']['password'] = self.__mail_password

            if 'smtp_server' not in self.__conf['mail']['from'] :
                raise Exception('Missing smtp server for external address')
            if 'port' not in self.__conf['mail']['from']['smtp_server'] :
                raise Exception('Missing smtp port for external address')
            if 'host' not in self.__conf['mail']['from']['smtp_server'] :
                raise Exception('Missing smtp host for external address')

            if 'imap_server' not in self.__conf['mail']['from'] :
                raise Exception('Missing smtp server for external address')
            if 'port' not in self.__conf['mail']['from']['imap_server'] :
                raise Exception('Missing smtp port for external address')
            if 'host' not in self.__conf['mail']['from']['imap_server'] :
                raise Exception('Missing smtp host for external address')

        if 'to' not in self.__conf['mail'] :
            self.__conf['mail']['to'] = 'nadege.lemperiere@gmail.com'

        # Update configuration from command line parameters
        if len(receiver) > 0 : self.__conf['mail']['to'] = receiver

        if 'pattern' not in self.__conf['mail'] :
            self.__conf['mail']['pattern'] = 'mail_pattern.txt'

        if 'calendar' not in self.__conf :
            self.__conf['calendar'] = {}
        if 'name' not in self.__conf['calendar'] :
            raise Exception('Missing calendar name to look for team session')
        if 'topic' not in self.__conf['calendar'] :
            self.__conf['calendar']['topic'] = 'Team Session'
        if 'days' not in self.__conf['calendar'] :
            self.__conf['calendar']['days'] = 1
        if 'time_zone' not in self.__conf['calendar'] :
            self.__conf['calendar']['time_zone'] = 'America/New_York'
        if 'full_day' not in self.__conf['calendar'] :
            self.__conf['calendar']['full_day'] = True
        else :
            self.__conf['calendar']['full_day'] = self.__conf['calendar']['full_day'] != 'False'

#pylint: disable=R0914, R1702
    def search_events(self):
        """
        Search and select events to be registered
        Parameters :
        Returns    :
        Throws     :
        """

        self.__events = []
        self.__logger.info('SEARCHING FOR UPCOMING EVENTS')

        try:

            calendar = self.__get_calendar_id(self.__conf['calendar']['name'], self.__token)
            events = self.__get_events(calendar, self.__conf['calendar']['days'], self.__token)

            for event in events :

                # Retrieve the dates for which event has already been registered
                last_reg = self.__get_registration_status(event['id'],self.__token)

                # Compute the timeslot for which the event shall be registered
                dates = self.__compute_registration_timeslot(
                    event,
                    self.__conf['calendar']['full_day'])

                # Compute the difference between the current registration state, and the new ones
                delta_start = timedelta(days=1)
                delta_end = timedelta(days=1)
                if 'start' in last_reg : delta_start = last_reg['start'] - dates['start']
                if 'end' in last_reg : delta_end = dates['end'] - last_reg['end']

                # Get names of students, coaches and mentors attending the event
                # Compare it with the last registration to get the new attendees
                attendees_list = self.__get_attendees(event, self.__contacts)
                attendees = { 'all' : attendees_list, 'new' : attendees_list}

                if 'students' in last_reg and 'coaches' in last_reg :
                    attendees['new'] = {'students' : [], 'coaches' : [], 'mentors': []}
                    for role in attendees['all'] :
                        for new in attendees['all'][role] :
                            found = False
                            if role in last_reg :
                                for old in last_reg[role] :
                                    if new['emailAddresses'][0]['address'] == old['emailAddresses'][0]['address'] :
                                        found = True
                            if not found : attendees['new'][role].append(new)

                # Check if event shall be registered, using its status and its subject
                # And only if there are people attending
                topic = self.__conf['calendar']['topic']
                if  'isCancelled' in event and not event['isCancelled'] and \
                    'subject' in event and topic in event['subject'] and \
                    len(attendees['all']['students']) + len(attendees['all']['coaches']) != 0 :

                    # Check if the event was already registered but dates have changed or
                    # if it has never been registered, in which case all the students
                    # and coaches shall be registered
                    if delta_start.total_seconds() > 0 or delta_end.total_seconds() > 0 :
                        attendees['new'] = attendees['all']
                        self.__events.append({'raw' : event, 'dates' : dates, 'attendees' : attendees})
                    # Check if the event was already registered at the correct time
                    # but attendees have changed, in this case only new attendees should be registered
                    elif len(attendees['new']['students']) != 0 or len(attendees['new']['coaches']) != 0 :
                        self.__events.append({'raw' : event, 'dates' : dates, 'attendees' : attendees})

        except Exception as e:
            self.__logger.error("Error retrieving events: %s", str(e))

        self.__logger.info("---> Found %d events",len(self.__events))
#pylint: enable=R0914, R1702

    def prepare_emails(self):
        """
        Build email content by replacing the pattern tags by the correct value
        Parameters :
        Returns    :
        Throws     :
        """

        self.__logger.info('FORMATTING EMAIL FROM TEMPLATE')

        # Read mail template file
        pattern_path = \
            path.normpath(path.join(path.dirname(__file__), self.__conf['mail']['pattern']))
        with open(pattern_path, encoding="utf-8") as file: template = file.read()

        # Format each event's email content
        for i_event, event in enumerate(self.__events):

            # Sent email with date corresponding to the configured timezone
            tz = ZoneInfo(self.__conf['calendar']['time_zone'])
            start = event['dates']['start'].astimezone(tz)
            end = event['dates']['end'].astimezone(tz)
            data = {
                'team': self.__conf['team'],
                'event_id': event['raw']['id'],
                'start_time': start.strftime('%A, %d. %B %Y at %I:%M%p'),
                'end_time': end.strftime('%A, %d. %B %Y at %I:%M%p'),
                'date': event['dates']['start'].strftime('%A, %d. %B %Y')
            }

            data['adults'] = \
                '\n'.join(f"- {c['displayName']}" for c in event['attendees']['new']['coaches'])
            data['students'] = \
                '\n'.join(f"- {s['displayName']}" for s in event['attendees']['new']['students'])
            data['mentors'] = \
                '\n'.join(f"- {m['displayName']}" for m in event['attendees']['new']['mentors'])

            # Replace placeholders in the template
            email = template
            for key, value in data.items():
                email = email.replace(f"{{{{{key}}}}}", value)
            self.__events[i_event]['mail'] = email

            self.__logger.info("---> Producing message of size %d", len(email))

    def send_emails(self):
        """
        Send emails using either microsoft API or a specific smtp and imap servers
        Parameters :
        Returns    :
        Throws     :
        """

        self.__logger.info('SENDING EMAILS TO %s', self.__conf['mail']['to'].upper())

        for event in self.__events:

            message = self.__format_email_object(event['mail'])
            has_been_sent = False

            if self.__conf['mail']['from']['address'] == self.__user['mail']:

                # Use Microsoft Graph API to send email
                try:

                    self.__logger.info('Sending email using Microsoft Graph')
                    self.__send_email_using_microsoft(
                        message,
                        self.__conf['mail']['to'],
                        self.__token)
                    has_been_sent = True
                except Exception as e:
                    self.__logger.error("Failed to send email : %s", str(e))

            else :

                # Use Dedicated SMTP server to send email
                try:

                    self.__logger.info('---> Sending email using smtp server coordinates')
                    self.__send_email_using_smtp_server(
                        message,
                        self.__conf['mail']['from']['address'],
                        self.__conf['mail']['to'],
                        self.__conf['mail']['from']['smtp_server'],
                        self.__conf['mail']['from']['imap_server'],
                        self.__conf['mail']['from']['password'])
                    has_been_sent = True
                except Exception as e:
                    self.__logger.error("Failed to send email : %s", str(e))

            if has_been_sent :

                self.__logger.info("--> Email sent successfully!")
                self.__update_registration_status(
                    event['raw']['id'],
                    self.__token,
                    event['dates'],
                    event['attendees']['all'])
                self.__logger.info("--> Event status updated!")

    def __get_token(self):
        """
        Get a token for the autorized user from a refresh token
        Parameters    :
        Returns (str) : The authentication token
        Throws        : Exception if the calendar list retrieval fails
        """

        # Data payload for the token request
        data = {
            'client_id': self.__credentials['client_id'],
            'client_secret': self.__credentials['client_secret'],
            'refresh_token': self.__credentials['refresh_token'],
            'grant_type': 'refresh_token',
            'redirect_uri': 'https://mantabots.org',
            'scope': Registration.s_scopes
        }

        # Make the POST request to acquire a new access token using the refresh token
        # USING THE COMMON ENDPOINT TO ACCESS PERSONAL ACCOUNTS IS KEY
        endpoint = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        response = self.__post(endpoint, data=data)

        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Error acquiring token: {response.content}")

        # Parse the JSON response
        token_response = response.json()

        # Acquire an access token
        if "access_token" not in token_response:
            raise Exception(f"Error acquiring token: {token_response.get('error_description')}")

        # Return the access token
        return token_response['access_token']

    def __get_user(self, token) :
        """
        Retrieve the authorized user information
        Parameters     :
            token (str) : Access token for the Microsoft Graph API
        Returns (dict) : The authorized user information
        Throws         : Exception if the calendar list retrieval fails
        """

        result = {}
        # Get my current microsoft email
        endpoint = "https://graph.microsoft.com/v1.0/me"
        headers = { 'Authorization': f'Bearer {token}','Content-Type': 'application/json'}

        response = self.__get(endpoint, headers=headers)

        if response.status_code == 200: result = response.json()
        else : raise Exception(f"Failed retrieving user with error : {response.content}")

        return result

    def __initialize_contacts(self, token):
        """
        Retrieve all the user contacts
        Parameters      :
            token (str) : Access token for the Microsoft Graph API
        Returns (array) : The list of all contacts
        Throws          : Exception if the calendar list retrieval fails
        """

        result = []
        self.__logger.info("---> Preloading contacts")

        # Define the endpoint and headers for the contacts request
        endpoint = "https://graph.microsoft.com/v1.0/me/contacts"
        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json' }

        # Send the request to get contacts
        response = self.__get(endpoint, headers=headers,
            params={'$top': 25, '$select': 'displayName,emailAddresses,jobTitle'})
        if response.status_code == 200: result = response.json().get('value', [])
        else : raise Exception(f"Failed retrieving contacts with error : {response.content}")

        self.__logger.info("---> Found %d contacts",len(result))

        return result

    def __get_calendar_id(self, name, token):
        """
        Retrieve the identifier of a calendar from its name
        Parameters    :
            name (str)  : The name of the calendar
            token (str) : Access token for the Microsoft Graph API
        Returns (str) : the calendar identifier
        Throws        : Exception if the calendar list retrieval fails
        """

        result = ''

        # Get all calendars
        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        endpoint = "https://graph.microsoft.com/v1.0/me/calendars"
        response = self.__get(endpoint, headers=headers)
        if response.status_code == 200: calendars = response.json().get('value', [])
        else : raise Exception(f"Failed retrieving calendars list with error : {response.content}")

        # Look for calendar with correct id
        for calendar in calendars :
            if calendar['name'] == name : result = calendar['id']
        if result == '' : self.__logger.error('Calendar %s not found', name)

        return result

    def __get_events(self, calendar, days, token):
        """
        Retrieve all events from a calendar
        Parameters      :
            calendar (str) : Identifier of the calendar to search
            days (int)     : Number of days to search for from now
            token (str)    : Access token for the Microsoft Graph API
        Returns (array) : list of the calendar events
        Throws          : Exception if the retrieval fails
        """

        result = []

        # Get all events
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendars/{calendar}/calendarview"
        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

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

        return result

    def __compute_registration_timeslot(self, event, is_full_day):
        """
        Compute registration timeslot for current event
        Parameters     :
            extension (dict) : Identifier of the event to update
        Returns (dict) : datetimes corresponding to the last registration dates (UTC)
        Throws         : Exception if the update fails
        """

        result = {}
        if 'start' in event:
            if 'dateTime' in event['start']:

                result['start'] = \
                    datetime.strptime(event['start']['dateTime'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                utc = ZoneInfo(event['start']['timeZone'])
                result['start'] = result['start'].replace(tzinfo=utc)

                result['end'] = \
                    datetime.strptime(event['end']['dateTime'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                utc = ZoneInfo(event['end']['timeZone'])
                result['end'] = result['end'].replace(tzinfo=utc)

                if event['isAllDay'] :
                    # Full days event appear to start at 00:00 UTC, even if created in another timezone
                    # Date data are not reliable, so we need to switch them to local timezone
                    local = ZoneInfo(self.__conf['calendar']['time_zone'])
                    result['start'] = result['start'].replace(tzinfo=local)
                    result['start'] = result['start'].astimezone(utc)
                    result['end'] = result['end'].replace(tzinfo=local)
                    result['end'] = result['end'] + timedelta(seconds=-1)
                    result['end'] = result['end'].astimezone(utc)

                if is_full_day :
                    local = ZoneInfo(self.__conf['calendar']['time_zone'])
                    result['start'] = result['start'].astimezone(local)
                    result['start'] = result['start'].replace(hour=0, minute=0, second=0)
                    result['start'] = result['start'].astimezone(utc)
                    result['end'] = result['end'].astimezone(local)
                    result['end'] = result['end'].replace(hour=23, minute=59, second=59)
                    result['end'] = result['end'].astimezone(utc)


        return result

    def __get_registration_status(self, identifier, token) :
        """
        Get registration status for the event (see __update_registration_status)
        Parameters     :
            identifier (str) : Identifier of the event to analyze
            token (str)      : Access token for the Microsoft Graph API
        Returns (dict) : Registration status
        Throws         : Exception if the update fails
        """

        result = {}

        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        endpoint = \
            f"https://graph.microsoft.com/v1.0/me/events/{identifier}/extensions/org.mantabots"
        response = self.__get(endpoint, headers=headers, params={})

        if response.status_code == 200:
            extension = loads(response.content.decode('utf-8'))

            if 'sent' in extension and extension['sent']:
                result['start'] = datetime.strptime(extension['start'],'%Y-%m-%dT%H:%M:%S%z')
                result['end'] = datetime.strptime(extension['end'],'%Y-%m-%dT%H:%M:%S%z')
                result['start'].replace(tzinfo=timezone.utc)
                result['end'].replace(tzinfo=timezone.utc)
                result['students'] = extension['students']
                result['coaches'] = extension['coaches']
                result['mentors'] = extension['mentors']

        return result

#pylint: disable=R1702
    def __get_attendees(self, event, contacts):
        """
        Update event attendees information from contacts information
        Parameters     :
            event (dict)    : Event to analyze for attendees
            contacts (dict) : List of contacts to look for attendees
        Returns (dict) : The list of students, mentors and coaches to register
        Throws         :
        """

        result = {'students': [], 'coaches': [], 'mentors': []}
        self.__logger.info('--> Getting attendees names from contacts list')

        if 'attendees' in event:
            for attendee in event['attendees']:
                # Search for attendees in contacts by matching email address
                for contact in contacts:
                    if 'emailAddresses' in contact:
                        for mail in contact['emailAddresses']:
                            if mail['address'] == attendee['emailAddress']['address'] :

                                # Append to list from job title
                                title = contact['jobTitle']
                                if title == 'Team Member':
                                    result['students'].append(contact)
                                elif title == 'Coach':
                                    result['coaches'].append(contact)
                                elif title == 'Mentor':
                                    result['mentors'].append(contact)

            self.__logger.info(
                "---> Found %d coaches %d students and %d mentors for event %s",
                len(result['coaches']),
                len(result['students']),
                len(result['mentors']),
                event.get('subject', 'No Subject')
            )

        return result

#pylint: enable=R1702

    def __format_email_object(self, email):
        """
        Separate the email content into subject and body
        Parameters     :
            email (str) : Email from pattern
        Returns (dict) : Message with subject and body
        Throws         : Exception if the update fails
        """
        result =  {'subject' : '', 'content' : ''}

        title_start_index = email.find('Subject:')
        title_end_index = email.find('\n', title_start_index)
        if title_start_index < 0 or title_end_index < 0:
            raise Exception('Failed to parse email title')
        result['subject'] = email[title_start_index + len('Subject:'):title_end_index].strip()

        content_start_index = title_end_index + 1
        content_end_index = len(email)
        if content_start_index < 0 or content_end_index < 0:
            raise Exception('Failed to parse email content')
        result['content'] = email[content_start_index:content_end_index]

        return result

    def __send_email_using_microsoft(self, message, recipient, token):
        """
        Send email from authorized user using Microsoft Graph API
        Parameters     :
            message (str)   : Email content
            recipient (str) : Recipient address
            token (str)     : Access token for the Microsoft Graph API
        Returns (dict) :
        Throws         : Exception if the sending fails
        """

        endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        email_message = {
            "message": {
                "subject": message['subject'],
                "body": { "contentType": "Text", "content": message['content'] },
                "toRecipients": [
                    { "emailAddress": { "address": recipient  } }
                ]
            },
            "saveToSentItems": "true"
        }

        # Send email via Microsoft Graph
        response  = self.__post(endpoint, headers=headers, json=email_message)
        if response.status_code != 202:
            raise Exception(f"Failed to send email : {response.content}")

#pylint: disable=R0913
    def __send_email_using_smtp_server(self, message, sender, recipient, smtp, imap, password):
        """
        Send email from user using SMTP server
        Parameters     :
            message (str)   : Email content
            sender (str)    : Sender address
            password(str)   : Sender password
            recipient (str) : Recipient address
            smtp (dict)     : SMTP server address and port
            imap (dict)     : IMAP server address and port
        Returns (dict) :
        Throws         : Exception if the sending fails
        """

        # Create the email message
        result = MIMEMultipart()
        result['From'] = sender
        result['To'] = recipient
        result['Subject'] = message['subject']
        result.attach(MIMEText(message['content'], 'plain'))

        # Send the email via SMTP server
        if self.__smtp: server = self.__smtp
        else : server = SMTP(smtp['host'], smtp['port'], timeout=10)

        server.ehlo()  # Identify ourselves to the SMTP server
        server.starttls()  # Secure the connection with TLS
        server.ehlo()  # Re-identify ourselves as an encrypted connection
        server.login(sender, password)
        self.__logger.info('---> Logged in smtp server')
        server.sendmail(sender, recipient, result.as_string())
        server.quit()

        # Copy the email in the sent folder
        if self.__imap: server = self.__imap
        else : server = IMAP4_SSL(imap['host'], imap['port'])
        server.login(sender, password)
        self.__logger.info('---> Logged in imap server')
        server.append('Sent', '\\Seen', Time2Internaldate(time()), result.as_bytes())
        server.logout()

#pylint: enable=R0913

    def __update_registration_status(self, identifier, token, dates, attendees):
        """
        Update event in calendar to mark it as sent, with the associated registration date
        Parameters     :
            identifier (str) : Identifier of the event to update
            token (str)      : Access token for the Microsoft Graph API
            dates (dict)     : Start and end date of the registration
            attendees (dict) : Lists of students, mentors and coaches
        Returns        : Nothing
        Throws         : Exception if the update fails
        """

        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        endpoint = f"https://graph.microsoft.com/v1.0/me/events/{identifier}/extensions"
        tz = ZoneInfo('UTC')

        custom_properties = {
            "@odata.type": "microsoft.graph.openTypeExtension",
            "extensionName": "org.mantabots",
            'sent'     : True,
            'start'    : dates['start'].astimezone(tz).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'end'      : dates['end'].astimezone(tz).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'students' : attendees['students'],
            'coaches'  : attendees['coaches'],
            'mentors'  : attendees['mentors']
        }
        response = self.__post(endpoint, headers=headers, json=custom_properties)

        if response.status_code != 201:
            raise Exception(f"Failed to update extensions with error : {response.text}")

# pylint: disable=W0107
# Main function using Click for command-line options
@group()
def main():
    """ Main click group """
    pass
# pylint: enable=W0107, W0719


@main.command()
@option('--conf', default='conf/conf.json')
@option('--microsoft', default='token.json')
@option('--mail', default='')
@option('--receiver', default='nadege.lemperiere@gmail.com')
@option('--sender', default='mantabots.infra@outlook.com')
def run(conf, microsoft, mail, receiver, sender):
    """ Script run function """
    registration = Registration(microsoft, mail)
    registration.configure(conf, receiver, sender)
    registration.search_events()
    registration.prepare_emails()
    registration.send_emails()


if __name__ == "__main__":
    config.fileConfig(logg_conf_path)
    main()
