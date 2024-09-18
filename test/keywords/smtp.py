# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" SMTP server mock for testing """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# System includes
from email          import message_from_string
from email.policy   import default

class MockSMTPServer:
    """ A mock class to simulate an SMTP server """

    def __init__(self, scenario):
        self.__scenario = {}
        self.__emails = []

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, address, password):
        pass

    def sendmail(self, from_addr, to_addr, message):

        msg = message_from_string(message, policy=default)

        subject = msg['Subject']

        content = ""
        if msg.is_multipart():
            # If the message is multipart, extract each part
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition"))

                # Check if the part is text/plain or text/html and not an attachment
                if content_type == "text/plain" and "attachment" not in disposition:
                    content = part.get_payload(decode=True).decode(part.get_content_charset())
                    break  # Stop after getting the first text/plain part
        else:
            # If not multipart, just get the payload
            content = msg.get_payload(decode=True).decode(msg.get_content_charset())

        self.__emails.append({
            'from'      : from_addr,
            'to'        : to_addr,
            'subject'   : subject,
            'content'   : content
        })

    def quit(self):
        pass

    def get_mails(self) :
        return self.__emails

