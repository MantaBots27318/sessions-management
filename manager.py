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
from base64 import urlsafe_b64encode
from json import load, loads
from smtplib import SMTP
from requests import get, post
from zoneinfo import ZoneInfo

# Email includes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Click includes
from click import option, group

# Microsoft includes
from msal import ConfidentialClientApplication, PublicClientApplication


# Logger configuration settings
logg_conf_path = path.normpath(path.join(path.dirname(__file__), 'conf/logging.conf'))


class Registration:
    """ Class managing registration workflow """

    # Define scopes for Microsoft Graph API
    s_scopes = [
        'Contacts.Read',
        'Calendars.ReadWrite',
        'Mail.Send'
    ]

    def __init__(self, microsoft, smtp, microsoft_service=None, smtp_server=None):
        """ Constructor """

        # Initialize logger
        self.__logger = getLogger('registration')
        self.__logger.info('INITIALIZING REGISTRATION')

        # Initialize credentials
        self.__credentials = {}
        token_conf_path = path.normpath(path.join(path.dirname(__file__), microsoft))
        with open(token_conf_path, encoding="utf-8") as file:
            self.__credentials = load(file)
        self.__smtp_password = smtp
        self.__conf = {}

        # Initialize Graph client
        self.__token = self.__get_token()
        self.__user = self.__get_user(self.__token)

        # Mock external API if required
        self.__smtp = smtp_server
        self.__microsoft = microsoft_service

        # Gather contacts list
        self.__contacts = self.__initialize_contacts(self.__token)

        # Initialize mail data
        self.__events = []

        self.__logger.info('---> Registration initialized')

    def configure(self, conf, receiver, sender):

        """ Read configuration from file """
        app_conf_path = path.normpath(path.join(path.dirname(__file__), conf))
        with open(app_conf_path, encoding="utf-8") as file:
            self.__conf = load(file)

        # Set default values and handle configuration logic
        self.__conf.setdefault('team', 'MantaBots')
        self.__conf.setdefault('mail', {}).setdefault('from', {'address': 'mantabots.infra@outlook.com'})
        self.__conf['mail'].setdefault('to', 'nadege.lemperiere@gmail.com')
        self.__conf['mail'].setdefault('pattern', 'mail_pattern.txt')
        self.__conf.setdefault('calendar', {}).setdefault('topic', 'Team Session')
        self.__conf['calendar'].setdefault('days', 1)
        self.__conf['calendar'].setdefault('full_day', True)
        
        if len(receiver) > 0:
            self.__conf['mail']['to'] = receiver
        if len(sender) > 0:
            self.__conf['mail']['from']['address'] = sender

    def search_events(self):
        """ Get all calendar events in the coming days """
        self.__events = []
        self.__logger.info('SEARCHING FOR UPCOMING EVENTS')

        headers = {'Authorization': f'Bearer {self.__token}','Content-Type': 'application/json'}

        try:

            # Get calendar
            cid = ''
            endpoint = f"https://graph.microsoft.com/v1.0/me/calendars"
            response = get(endpoint, headers=headers)
            if response.status_code == 200: calendars = response.json().get('value', [])

            for calendar in calendars :
                if calendar['name'] == self.__conf['calendar']['name'] : cid = calendar['id']

            if cid == '' : 
                self.__logger.error('Calendar %s not found', self.__conf['calendar']['name'])

            # Define the endpoint and headers for the contacts request
            endpoint = f"https://graph.microsoft.com/v1.0/me/calendars/{cid}/calendarview"
            
            params = {
                'startDateTime': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'endDateTime': (datetime.now(timezone.utc) + timedelta(days=self.__conf['calendar']['days'])).isoformat(timespec='seconds'),
                '$orderby': 'start/dateTime',
                '$top': 10
            }

            # Send the request to get calendar events
            response = get(endpoint, headers=headers, params=params)
            if response.status_code == 200:

                # Get extended properties containing sent status
                events = response.json().get('value', [])
                for event in events :
                    
                    dates = self.__compute_timeslot(event, self.__conf['calendar']['full_day'])
                
                    endpoint = f"https://graph.microsoft.com/v1.0/me/events/{event['id']}/extensions/org.mantabots"
                    response = get(endpoint, headers=headers, params={})
                    print(loads(response.content.decode('utf-8')))
                    
                    if response.status_code == 200:

                        # Check if the event has already been registered, and if it needs to be updated
                        last_dates = \
                            self.__read_last_dates(loads(response.content.decode('utf-8')))

                        shall_be_registered_once_again = False
                        delta_start = timedelta(days=1)
                        delta_end = timedelta(days=1)
                        if 'start' in last_dates :
                            delta_start = last_dates['start'] - dates['start']
                        if 'end' in last_dates :
                            delta_end = dates['end'] - last_dates['end']

                        if delta_start.total_seconds() > 0 or delta_end.total_seconds() > 0 :
                            shall_be_registered_once_again = True

                        # Check if event shall be registered
                        if 'isCancelled' in event and \
                        not event['isCancelled']  and \
                        'subject' in event and \
                        self.__conf['calendar']['topic'] in event['subject'] and \
                        shall_be_registered_once_again :
                            self.__events.append({'raw' : event, 'dates' : dates})

                        print(shall_be_registered_once_again)

                    else :
                        # No extended properties means never been processed
                        self.__events.append({'raw' : event, 'dates' : dates})
            else:
                self.__logger.error(f"Error retrieving events: {response.status_code} - {response.text}")

        except Exception as e:
            self.__logger.error(f"Error retrieving calendar: {str(e)}")

        self.__logger.info(f"---> Found {len(events)} events.")

    def get_attendees(self):
        """ List attendees for selected events """
        self.__logger.info('GETTING ATTENDEES INFO FROM CONTACTS')

        for i_event, event in enumerate(self.__events):
            attendees = {'students': [], 'coaches': [], 'mentors': []}

            if 'attendees' in event['raw']:
                for attendee in event['raw']['attendees']:
                    for contact in self.__contacts:
                        # Match attendee emails with contacts
                        if 'emailAddresses' in contact:
                            for mail in contact['emailAddresses']:
                                if mail['address'] == attendee['emailAddress']['address']:
                                    title = contact['jobTitle']
                                    if title == 'Team Member':
                                        attendees['students'].append(contact)
                                    elif title == 'Coach':
                                        attendees['coaches'].append(contact)
                                    elif title == 'Mentor':
                                        attendees['mentors'].append(contact)

                self.__logger.info(
                    "---> Found %d coaches %d students and %d mentors for event %s",
                    len(attendees['coaches']),
                    len(attendees['students']),
                    len(attendees['mentors']),
                    event['raw'].get('subject', 'No Subject')
                )

            self.__events[i_event]['attendees'] = attendees

    def prepare_emails(self):
        """ Build email content by replacing the tags by the current value """
        self.__logger.info('FORMATTING EMAIL FROM TEMPLATE')

        # Read mail template file
        pattern_path = path.normpath(path.join(path.dirname(__file__), self.__conf['mail']['pattern']))
        with open(pattern_path, encoding="utf-8") as file:
            template = file.read()

        # Format each event's email content
        for i_event, event in enumerate(self.__events):
            data = {
                'team': self.__conf['team'],
                'event_id': event['raw']['id'],
                'start_time': event['dates']['start'].strftime('%A, %d. %B %Y at %I:%M%p'),
                'end_time': event['dates']['end'].strftime('%A, %d. %B %Y at %I:%M%p'),
                'date': event['dates']['start'].strftime('%A, %d. %B %Y')
            }

            data['adults'] = '\n'.join(f"- {c['displayName']}" for c in event['attendees']['coaches'])
            data['students'] = '\n'.join(f"- {s['displayName']}" for s in event['attendees']['students'])
            data['mentors'] = '\n'.join(f"- {m['displayName']}" for m in event['attendees']['mentors'])

            # Replace placeholders in the template
            email = template
            for key, value in data.items():
                email = email.replace(f"{{{{{key}}}}}", value)
            self.__events[i_event]['mail'] = email

            self.__logger.info("---> Producing message of size %d", len(email))

    def send_emails(self):
        """ Sending emails to recipients """
        self.__logger.info('SENDING EMAILS TO %s', self.__conf['mail']['to'].upper())

        
        for i_event, event in enumerate(self.__events):

            title_start_index = event['mail'].find('Subject:')
            title_end_index = event['mail'].find('\n', title_start_index)
            content_start_index = title_end_index + 1
            content_end_index = len(event['mail'])
            message_text = event['mail'][content_start_index:content_end_index]
            has_been_sent = False

            if self.__conf['mail']['from']['address'] == self.__user['mail']:
                try:
                    
                    endpoint = f"https://graph.microsoft.com/v1.0/me/sendMail"
                    headers = {
                        'Authorization': f'Bearer {self.__token}',
                        'Content-Type': 'application/json'
                    }

                    email_message = {
                        "message": {
                            "subject": event['mail'][title_start_index + len('Subject:'):title_end_index].strip(),
                            "body": { "contentType": "Text", "content": message_text },
                            "toRecipients": [
                                { "emailAddress": { "address": self.__conf['mail']['to']  } }
                            ]
                        },
                        "saveToSentItems": "true"  # Optional: Save a copy in the sent items folder
                    }
                    response  = post(endpoint, headers=headers, json=email_message)
                    if response.status_code == 202:
                        has_been_sent = True
                    else:
                        self.__logger.error("Failed to send email : %s",response.content)
                    # Send via Microsoft Graph (or another service if needed)
                    self.__logger.info('Sent email using Microsoft Graph')
                except Exception as e:
                    self.__logger.error("Failed to send email : %s", str(e))

            else :

                self.__logger.info('---> Sending email using smtp server coordinates')

                # Create the email message
                message = MIMEMultipart()
                message['From'] = self.__conf['mail']['from']['address']
                message['To'] = self.__conf['mail']['to']
                message['Subject'] = \
                    event['mail'][title_start_index + len('Subject:'):title_end_index].strip()

                # Attach the body with MIMEText
                message.attach(MIMEText(message_text, 'plain'))

                # Send the email via SMTP server
                try:
                    if self.__smtp:
                        server = self.__smtp
                    else :
                        server = SMTP(
                        self.__conf['mail']['from']['smtp_server'],
                        self.__conf['mail']['from']['smtp_port'], timeout=10)
                    server.ehlo()  # Identify ourselves to the SMTP server
                    server.starttls()  # Secure the connection with TLS
                    server.ehlo()  # Re-identify ourselves as an encrypted connection
                    server.login(
                        self.__conf['mail']['from']['address'],
                        self.__conf['mail']['from']['password'])
                    self.__logger.info('---> Logged in')
                    server.sendmail(
                        self.__conf['mail']['from']['address'],
                        self.__conf['mail']['to'], message.as_string())
                    self.__logger.info("Email sent successfully!")
                    has_been_sent = True

                except Exception as e:
                    self.__logger.error("Failed to send email : %s",str(e))

            
            if has_been_sent :

                endpoint = f"https://graph.microsoft.com/v1.0/me/events/{event['raw']['id']}/extensions"
                
                # Update event in calendar to mark as sent
                start_day = event['dates']['start'].strftime('%A, %d. %B %Y')
                end_day = event['dates']['end'].strftime('%A, %d. %B %Y')
                start_time = event['dates']['start'].strftime('%I:%M%p')
                end_time = event['dates']['end'].strftime('%I:%M%p')
                custom_properties = {
                    "@odata.type": "microsoft.graph.openTypeExtension",
                    "extensionName": "org.mantabots",
                    'sent'  : True,
                    'start' : f"{start_day} at {start_time}",
                    'end'   : f"{end_day} at {end_time}"
                }
                post(endpoint, headers=headers, json=custom_properties)


    def __get_token(self):
        """Initialize Microsoft Graph client"""

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
        response = post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data=data)

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
        """ Get information on the microsoft user currently using microsoft interface """

        result = {}
        # Get my current microsoft email 
        endpoint = "https://graph.microsoft.com/v1.0/me"
        headers = { 'Authorization': f'Bearer {token}','Content-Type': 'application/json'}

        response = get(endpoint, headers=headers)
        if response.status_code == 200:
            result = response.json()
        else :
            self.__logger.error("Failed to retrieve user information : %s", str(response.content))

        return result
    
    def __initialize_contacts(self, token):
        """ Gather all contacts in the account contacts list """

        result = []

        self.__logger.info("---> Preloading contacts")
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/contacts"
        headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json' }

        try:
            # Define the endpoint and headers for the contacts request

            # Send the request to get contacts
            response = get(endpoint, headers=headers, params={'$top': 25, '$select': 'displayName,emailAddresses,jobTitle'})
            if response.status_code == 200:
                result = response.json().get('value', [])
            else:
                self.__logger.error(f"Error retrieving contacts: {response.status_code} - {response.text}")

        except Exception as e:
            self.__logger.error(f"Error retrieving contacts: {str(e)}")
            return []

        self.__logger.info("---> Found %d contacts",len(result))

        return result

    def __compute_timeslot(self, event, is_full_day):
        """ Compute event registration timeslot from event data and configuration """

        result = {}
        if 'start' in event:
            if 'dateTime' in event['start']:

                result['start'] = datetime.strptime(event['start']['dateTime'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                timezone = ZoneInfo(event['start']['timeZone'])
                result['start'] = result['start'].replace(tzinfo=timezone)

                result['end'] = datetime.strptime(event['end']['dateTime'][:26], '%Y-%m-%dT%H:%M:%S.%f')
                timezone = ZoneInfo(event['end']['timeZone'])
                result['end'] = result['end'].replace(tzinfo=timezone)

                if is_full_day or event['isAllDay']:
                    result['start'] = result['start'].replace(hour=0, minute=0, second=0)
                    result['end'] = result['end'].replace(hour=23, minute=59, second=59)


        return result

    def __read_last_dates(self,extension) :
        """ """
        result = {}

        if 'sent' in extension and \
            extension['sent'] == 'true':
            result['start'] = \
                datetime.strptime(extension['start'],
                    '%A, %d. %B %Y at %I:%M%p')
            result['end'] = \
                datetime.strptime(extension['end'],
                    '%A, %d. %B %Y at %I:%M%p')

        return result


# Main function using Click for command-line options
@group()
def main():
    """ Main click group """
    pass


@main.command()
@option('--conf', default='conf/conf.json')
@option('--microsoft', default='token.json')
@option('--smtp', default='')
@option('--receiver', default='nadege.lemperiere@gmail.com')
@option('--sender', default='mantabots.infra@outlook.com')
def run(conf, microsoft, smtp, receiver, sender):
    """ Script run function """
    registration = Registration(microsoft, smtp)
    registration.configure(conf, receiver, sender)
    registration.search_events()
    registration.get_attendees()
    registration.prepare_emails()
    registration.send_emails()


if __name__ == "__main__":
    config.fileConfig(logg_conf_path)
    main()
