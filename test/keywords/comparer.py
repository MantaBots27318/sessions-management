# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Registration workflow keywords io functions """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# System includes
from zoneinfo  import ZoneInfo
from json      import load
from os        import path
from datetime  import datetime, timedelta, timezone
from zoneinfo  import ZoneInfo


# Robotframework includes
from robot.api               import logger as logger
ROBOT = False


class Comparer :
    """ Namespace for comparison functions """

    def compare_emails_number(expected, actual) :
        """ Compare the number of emails sent """

        logger.info(f'Sent {len(expected['data']['mails'])} emails [reference {len(actual['smtp'].get_mails())}]')

        if len(expected['data']['mails']) != len(actual['smtp'].get_mails()) :
            raise Exception('Different number of emails sent')

    def compare_registration(expected, actual, timezone, is_full) :

        dates = Comparer.compute_dates_as_string(actual['event'], timezone, is_full)

        if not 'registration' in actual['event'] : raise Exception('Event not updated after email sent')
        if not 'sent' in actual['event']['registration'] : raise Exception('Event not updated after email sent')
        if not 'start' in actual['event']['registration'] : raise Exception('Event not updated after email sent')
        if not 'end' in actual['event']['registration'] : raise Exception('Event not updated after email sent')
        if not 'students' in actual['event']['registration'] : raise Exception('Event not updated after email sent')
        if not 'adults' in actual['event']['registration'] : raise Exception('Event not updated after email sent')

        start_date_utc   = dates['start']['utc'].strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        end_date_utc     = dates['end']['utc'].strftime('%Y-%m-%dT%H:%M:%S.%f%z')

        logger.debug(actual['event']['registration'])
        logger.debug(start_date_utc)
        logger.debug(end_date_utc)

        if not actual['event']['registration']['sent'] : raise Exception('Event sent status is not true')
        if actual['event']['registration']['start'] != start_date_utc : raise Exception('Start date does not match email')
        if actual['event']['registration']['end'] != end_date_utc : raise Exception('End date does not match email')


    def compare_email(expected, actual, timezone, is_full) :
        """ Compare the content of emails sent """

        dates = Comparer.compute_dates_as_string(actual['event'], timezone, is_full)
        local_test = Comparer.build_reference_from_pattern(expected, dates)

        logger.debug(local_test['subject'])
        logger.debug(actual['mail']['subject'])
        logger.debug(local_test['content'])
        logger.debug(actual['mail']['content'])

        if expected['from'] != actual['mail']['from'] or \
           expected['to'] != actual['mail']['to'] or \
           local_test['subject'] != actual['mail']['subject'] or \
           local_test['content'] != actual['mail']['content'] :
            raise Exception('Mail does not match')


    def compute_dates_as_string(event, local, is_full) :

        result = {
            'start': {'utc' : None, 'local' : None},
            'end':   {'utc' : None, 'local' : None}
        }

        tz = ZoneInfo('UTC')
        start_date = event['start']['date']
        end_date = event['end']['date']

        if event['full_day'] == 'true' : end_date = end_date + timedelta(seconds=-1)
        elif is_full and event['full_day'] != 'true':
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date + timedelta(seconds=-1)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

        result['start']['utc']   = start_date.astimezone(tz)
        result['end']['utc']   = end_date.astimezone(tz)
        result['start']['local'] = start_date.astimezone(local)
        result['end']['local']   = end_date.astimezone(local)

        return result

    def build_reference_from_pattern(expected, dates) :

        result = {'subject' : '', 'content' : ''}

        result['subject'] = expected['subject'].replace(
            '{{start_date}}',
            dates['start']['local'].strftime('%A, %d. %B %Y')
        )
        result['subject'] = result['subject'].replace(
            '{{end_date}}',
            dates['end']['local'].strftime('%A, %d. %B %Y')
        )
        result['content'] = expected['content'].replace(
            '{{start_date}}',
            dates['start']['local'].strftime('%A, %d. %B %Y'))
        result['content'] = result['content'].replace(
            '{{end_date}}',
            dates['end']['local'].strftime('%A, %d. %B %Y'))

        result['subject'] = result['subject'].replace(
            '{{start_time}}',
            dates['start']['local'].strftime('%I:%M%p'))
        result['subject'] = result['subject'].replace(
            '{{end_time}}',
            dates['end']['local'].strftime('%I:%M%p'))
        result['content'] = result['content'].replace(
            '{{start_time}}',
            dates['start']['local'].strftime('%I:%M%p'))
        result['content'] = result['content'].replace(
            '{{end_time}}',
            dates['end']['local'].strftime('%I:%M%p'))

        return result
