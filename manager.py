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
from logging    import config, getLogger
from datetime   import datetime, timedelta, timezone
from os         import path
from base64     import urlsafe_b64encode
from json       import load
from smtplib    import SMTP

# Email includes
from email.mime.text        import MIMEText
from email.mime.multipart   import MIMEMultipart

# Click includes
from click import option, group

# Google includes
from google.auth.transport.requests import Request
from google.oauth2.credentials      import Credentials
from googleapiclient.discovery      import build

# Logger configuration settings
logg_conf_path = path.normpath(path.join(path.dirname(__file__), 'conf/logging.conf'))

#pylint: disable=R0902, E1101
class Registration:
    """ Class managing registration workflow """

    # Define scopes for the Google APIs
    s_scopes = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/contacts.readonly',
        'https://www.googleapis.com/auth/gmail.send' 
    ]

    def __init__(self, google, smtp, google_service=None, smtp_server=None):
        """ Constructor """

        # Initialize logger
        self.__logger = getLogger('registration')
        self.__logger.info('INITIALIZING REGISTRATION')

        # Initialize credentials
        self.__credentials_file       = path.normpath(path.join(path.dirname(__file__), google))
        self.__credentials            = None
        self.__smtp_password          = smtp
        self.__conf                   = {}

        # Mocked services (Injected for testing)
        self.__google = google_service
        self.__smtp = smtp_server

        # Gather contacts list
        self.__contacts = self.__initialize_contacts()

        # Initialize mail data
        self.__events    = []

        self.__logger.info('---> Registration initialized')

    def configure(self, conf, receiver, sender) :
        """ Read configuration from file """

        # Load configuration file
        app_conf_path = path.normpath(path.join(path.dirname(__file__), conf))
        with open(app_conf_path, encoding="utf-8") as file:
            self.__conf = load(file)

        # Check configuration content and add default values if needed
        if 'team' not in self.__conf :
            self.__conf['team'] = 'MantaBots'

        if 'mail' not in self.__conf :
            self.__conf['mail'] = {}

#pylint: disable=W0719
        if 'from' not in self.__conf['mail'] :
            # Use gmail address through google api
            self.__conf['mail']['from'] = { "address" : "mantabots.infra@gmail.com"}
        if 'address' not in self.__conf['mail']['from'] :
            self.__conf['mail']['from'] = { "address" : "mantabots.infra@gmail.com"}
        if self.__conf['mail']['from']['address'] != "mantabots.infra@gmail.com" :
            # We need the smtp server configuration
            if len(self.__smtp_password) == 0 :
                raise Exception('Missing password for external address')
            self.__conf['mail']['from']['password'] = self.__smtp_password
            if 'smtp_server' not in self.__conf['mail']['from'] :
                raise Exception('Missing smtp server for external address')
            if 'smtp_port' not in self.__conf['mail']['from'] :
                raise Exception('Missing smtp port for external address')

        if 'to' not in self.__conf['mail'] :
            self.__conf['mail']['to'] = 'nadege.lemperiere@gmail.com'

        if 'pattern' not in self.__conf['mail'] :
            self.__conf['mail']['pattern'] = 'mail_pattern.txt'

        if 'calendar' not in self.__conf :
            self.__conf['calendar'] = {}
        if 'id' not in self.__conf['calendar'] :
            raise Exception('Missing calendar id to look for team session')
        if 'topic' not in self.__conf['calendar'] :
            self.__conf['calendar']['topic'] = 'Team Session'
        if 'days' not in self.__conf['calendar'] :
            self.__conf['calendar']['days'] = 1
        if 'full_day' not in self.__conf['calendar'] :
            self.__conf['calendar']['full_day'] = True
        else :
            self.__conf['calendar']['full_day'] = self.__conf['calendar']['full_day'] != 'False'

        if len(receiver) > 0 : self.__conf['mail']['to'] = receiver
        if len(sender) > 0 : self.__conf['mail']['from']['address'] = sender

#pylint: enable=W0719

    def search_events(self):
        """ Get all calendar events in the coming days """

        self.__events = []
        self.__logger.info('SEARCHING FOR UPCOMING EVENTS')

        try:
            # Get calendar details
            service = self.__initialize_service('calendar', 'v3')
            calendar = service.calendars().get(calendarId=self.__conf['calendar']['id']).execute()
            self.__logger.info(
                "---> Analyzing calendar %s containing %s",
                calendar['summary'],calendar.get('description', 'No description'))

            # List upcoming events
            now = datetime.now(timezone.utc).isoformat()
            end = (datetime.now(timezone.utc) + \
                  timedelta(days=self.__conf['calendar']['days'])).isoformat()
            events_result = service.events().list(calendarId=self.__conf['calendar']['id'],
                timeMin=now, timeMax=end, singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])

            # Look for confirmed events in the timeframe
            for event in events:

                dates = self.__compute_timeslot(event, self.__conf['calendar']['full_day'])

                # Check if the event has already been registered, and if it needs to be updated
                last_dates = self.__read_last_dates(event)

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
                if event.get("status") == 'confirmed' and \
                   self.__conf['calendar']['topic'] in event.get('summary') and \
                   shall_be_registered_once_again :
                    self.__events.append({'raw' : event, 'dates' : dates})

            self.__logger.info(
                "---> Found %d events with topic %s in the next %d days",
                len(self.__events), self.__conf['calendar']['topic'],
                self.__conf['calendar']['days'])

        except Exception as e:
            self.__logger.error("Error retrieving calendar: %s",str(e))

#pylint: disable=R1702
    def get_attendees(self):

        """ List attendees for selected event """
        self.__logger.info('GETTING ATTENDEES INFO FROM CONTACTS')

        for i_event,event in enumerate(self.__events) :

            attendees = {
                'students' : [],
                'coaches'  : [],
                'mentors'  : []
            }

            if 'attendees' in event['raw']:
                for attendee in event['raw']['attendees']:
                    for contact in self.__contacts :

                        # Get title
                        title = ''
                        if 'organizations' in contact :
                            for organization in contact['organizations'] :
                                title = organization['title']

                        # Check if email address match attendee one
                        if 'emailAddresses' in contact :
                            for mail in contact['emailAddresses'] :
                                if 'value' in mail :
                                    if mail['value'] == attendee['email'] :
                                        if title == 'Team Member' :
                                            attendees['students'].append(contact)
                                        elif title == 'Coach' :
                                            attendees['coaches'].append(contact)
                                        elif title == 'Mentor' :
                                            attendees['mentors'].append(contact)

                self.__logger.info(
                    "---> Found %d coaches %d students and %d mentors for event %s",
                    len(attendees['coaches']),
                    len(attendees['students']),
                    len(attendees['mentors']),
                    self.__events[i_event]['raw'].get('summary')
                )

            self.__events[i_event]['attendees'] = attendees

#pylint: disable=R1702

#pylint: disable=R0914
    def prepare_emails(self) :
        """ Build email content by replacing the tags by the current value"""

        self.__logger.info('FORMATTING EMAIL FROM TEMPLATE')

        # Read mail template file
        pattern_path = path.normpath(
            path.join(path.dirname(__file__), self.__conf['mail']['pattern']))
        with open(pattern_path, encoding="utf-8") as file:
            template = file.read()

        self.__logger.info(
            "---> Template read from file %s containing %d characters",
            self.__conf['mail']['pattern'], len(template)
        )

        # Gather data
        for i_event,event in enumerate(self.__events) :

            data = {}
            email = template

            data['team'] = self.__conf['team']
            data['event_id'] = event['raw']['id']

            # Formatting date information
            start = event['dates']['start']
            end = event['dates']['end']
            data['start_time'] = \
                f"{start.strftime('%A, %d. %B %Y')} at {start.strftime('%I:%M%p')}"
            data['end_time'] = \
                f"{end.strftime('%A, %d. %B %Y')} at {end.strftime('%I:%M%p')}"
            data['date'] = f"{event['dates']['start'].strftime('%A, %d. %B %Y')}"

            # Formatting coaches list
            if 'coaches' in event['attendees'] :
                coaches = ''
                for coach in event['attendees']['coaches'] :
                    if 'names' in coach and 'displayName' in coach['names'][0]:
                        coaches = coaches + f'- {coach['names'][0]['displayName']}\n'
                data['adults'] = coaches

            # Formatting students list
            if 'students' in event['attendees'] :
                students = ''
                for student in event['attendees']['students'] :
                    if 'names' in student and 'displayName' in student['names'][0]:
                        students = students + f'- {student['names'][0]['displayName']}\n'
                data['students'] = students

            # Formatting mentors list
            if 'mentors' in event['attendees'] :
                mentors = ''
                for mentor in event['attendees']['mentors'] :
                    if 'names' in mentor and 'displayName' in mentor['names'][0]:
                        mentors = mentors + f'- {mentor['names'][0]['displayName']}\n'
                data['mentors'] = mentors

            for key, value in data.items():
                email = email.replace(f"{{{{{key}}}}}", value)
            self.__events[i_event]['mail'] = email

            self.__logger.info(
                "---> Producing message of size %d",
                len(email)
            )

#pylint: disable=R0915
    def send_emails(self) :
        """ Sending emails to recipients """

        mail_service = self.__initialize_service('gmail', 'v1')
        calendar_service = self.__initialize_service('calendar', 'v3')
        self.__logger.info('SENDING EMAILS TO %s',self.__conf['mail']['to'].upper())

        for i_event,event in enumerate(self.__events) :

            title_start_index = event['mail'].find('Subject:')
            title_end_index = event['mail'].find('\n', title_start_index)
            content_start_index = title_end_index + 1
            content_end_index = len(event['mail'])
            message_text = event['mail'][content_start_index:content_end_index]
            has_been_sent = False

            if self.__conf['mail']['from']['address'] == "mantabots.infra@gmail.com" :

                self.__logger.info('---> Sending email using google API')

                try :
                    message = MIMEText(message_text)
                    message['subject'] = \
                        event['mail'][title_start_index + len('Subject:'):title_end_index].strip()
                    message['to'] = self.__conf['mail']['to']
                    message['from'] = self.__conf['mail']['from']['address']
                    raw = urlsafe_b64encode(message.as_bytes()).decode()
                    message_body = {'raw': raw}
                    mail_service.users().messages().send(userId='me', body=message_body).execute()
                    has_been_sent = True

                except Exception as e:
                    self.__logger.error("Failed to send email : %s",str(e))


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
                # Update event in calendar to mark as sent
                start_day = event['dates']['start'].strftime('%A, %d. %B %Y')
                end_day = event['dates']['end'].strftime('%A, %d. %B %Y')
                start_time = event['dates']['start'].strftime('%I:%M%p')
                end_time = event['dates']['end'].strftime('%I:%M%p')
                self.__events[i_event]['raw']['extendedProperties'] = {
                    'private' : {
                        'sent'  : True,
                        'start' : f"{start_day} at {start_time}",
                        'end'   : f"{end_day} at {end_time}"
                    }
                }
                calendar_service.events().update(
                    calendarId=self.__conf['calendar']['id'], eventId=event['raw']['id'],
                    body=event['raw']).execute()

#pylint: enable=R0914,R0915

    def __initialize_credentials(self):
        """ Gather credentials and initialize the required Google API service """

        # Initialize credentials for authorized user
        if self.__credentials and self.__credentials.expired and self.__credentials.refresh_token:
            self.__logger.info("---> Refreshing oauth user token")
            self.__credentials.refresh(Request())
        else:
            self.__credentials = Credentials.from_authorized_user_file(
                self.__credentials_file, scopes=Registration.s_scopes
            )

    def __initialize_service(self, api, version):
        """ Initialize the Google API service """

        result = None
        self.__initialize_credentials()
        if self.__google:
            # Use the injected mock service if provided
            result = self.__google.build_service(api, version, credentials=self.__credentials)
        else:
            result = build(api, version, credentials=self.__credentials, cache_discovery=False)

        return result

    def __initialize_contacts(self):
        """ Gather all contacts in the account contacts list """
        result = []

        self.__logger.info("---> Preloading contacts")

        service = self.__initialize_service('people', 'v1')
        if not service:
            self.__logger.error("Failed to initialize People API service")
            return result

        try:
            results = service.people().connections().list(
                resourceName='people/me', pageSize=100,
                personFields='names,emailAddresses,organizations'
            ).execute()

            connections = results.get('connections', [])
            result = connections
            self.__logger.info("---> Found %d contacts",len(result))

        except Exception as e:
            self.__logger.error("Error retrieving contacts: %s",str(e))

        return result

    def __compute_timeslot(self, event, is_full_day) :
        """ Compute event registration timeslot from event data and configuration """

        result = {}

        if 'start' in event :
            if 'date' in event['start'] :

                # Full day event
                result['start'] = datetime.strptime(event['start']['date'], '%Y-%m-%d')
                result['end'] = datetime.strptime(event['end']['date'], '%Y-%m-%d')

            elif 'dateTime' in event['start'] :

                result['start']  = \
                    datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
                result['end']  = \
                    datetime.strptime(event['end']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
                if is_full_day :
                    result['start'] = result['start'].replace(hour=0,minute=0,second=0)
                    result['end'] = result['end'].replace(hour=23,minute=59,second=59)

        return result

    def __read_last_dates(self,event) :
        """ """
        result = {}

        if 'extendedProperties' in event :
            if 'private' in event['extendedProperties'] :
                if 'sent' in event['extendedProperties']['private'] and \
                    event['extendedProperties']['private']['sent'] == 'true':

                    result['start'] = \
                        datetime.strptime(event['extendedProperties']['private']['start'],
                            '%A, %d. %B %Y at %I:%M%p')
                    result['end'] = \
                        datetime.strptime(event['extendedProperties']['private']['end'],
                            '%A, %d. %B %Y at %I:%M%p')

        return result

#pylint: enable=R0902, E1101

#pylint: disable=W0107
@group()
def main():
    """ Main click group """
    pass
#pylint: enable=W0107

@main.command()
@option('--conf', default='conf/conf.json')
@option('--google', default='token.json')
@option('--smtp', default='')
@option('--receiver', default='nadege.lemperiere@gmail.com')
@option('--sender', default='mantabots.infra@gmail.com')
def run(conf, google, smtp, receiver, sender):

    """ Script run function """
    registration = Registration(google, smtp)
    registration.configure(conf, receiver, sender)
    registration.search_events()
    registration.get_attendees()
    registration.prepare_emails()
    registration.send_emails()


if __name__ == "__main__":
    config.fileConfig(logg_conf_path)
    main()
