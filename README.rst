===================
sessions-management
===================

About The Project
=================

This project automates robotics session notifications to the French American School of New York
who generously host the MantaBots team


.. image:: https://badgen.net/github/checks/MantaBots27318/sessions-management
   :target: https://github.com/MantaBots27318/sessions-management/actions/workflows/release.yml
   :alt: Status
.. image:: https://badgen.net/github/commits/MantaBots27318/sessions-management/main
   :target: https://github.com/MantaBots27318/sessions-management
   :alt: Commits
.. image:: https://badgen.net/github/last-commit/MantaBots27318/sessions-management/main
   :target: https://github.com/MantaBots27318/sessions-management
   :alt: Last commit

Built And Packaged With
-----------------------

.. image:: https://img.shields.io/static/v1?label=python&message=3.12.6rc1&color=informational
   :target: https://www.python.org/
   :alt: Python

Principle
=========

We have two robotics team, one using a Google account and another using a Microsoft account. Both of them have to report to the office manager when they plan on having a session. The goal of this project is to automate this email based on the content of their calendar and contacts list. We want this script to be able to use both Google API and Microsoft API.

This python scripts performs the following steps :

1) Analyze a calendar to gather events using either Microsoft Graph API or Google API:

   - Which are due to happen in the next N days
   - Whose Summary contains a given topic
   - Which have not been registered yet, or whose registration date have changed ( see below )
   - Whose registration date has not changed, but who have additional attendees

2) Select the name of the attendees from a contact list using Microsoft Graph API or Google API:

   - Fron the selected event, attendees email addresses are selected
   - The email address are matched against contact list
   - The contacts are marked as students if one of their tags is Student, as adults if one of their tags is Adult.

3) Build a registration email from the pattern text file

   - Replacing {{adults}}, {{students}} by the attendees names
   - Replacing {{start_time}} and {{end_time}} by the event start and end time
   - Replacing {{team}} by the team name
   - Replacing {{date}} by the start time day

4) Sends the email to the recipient using either an external smtp server, the Microsoft Graph API or the Google Gmail API

5) Update calendar events extended properties to mark them as sent, with the associated registration date

Getting Started
===============

Prerequisites
-------------

Depending on your use case, check either :

- The `Microsoft Prerequisites`_
- The `Google Prerequisites`_

.. _`Microsoft Prerequisites`: doc/microsoft-configuration.rst
.. _`Google Prerequisites`: doc/google-configuration.rst

Configuration
-------------

The script uses both a configuration file for non secret value, and command line to input secret values

The non secret configuration data are located into a `configuration file`_
The configuration file format is given below :

.. code-block:: JSON

   {
      "team" : <Team name to copy into email>,
      "mail" : {
         "from" : {
            "smtp_server" : {
                "host" : <smtp server address if not using Microsoft>,
                "port" : <smtp server port if not using Microsoft>
            },
            "imap_server" : {
                "host" : <imap server address if not using Microsoft>,
                "port" : <imap server port if not using Microsoft>
            },
            "address"     : <sender address>
         },
         "to" : <recipient address>,
         "pattern" : <mail pattern text file, see `example`_>,
      },
      "calendar" : {
         "name" : <Microsoft calendar name>,
         "topic" : <topic to look for in events to register>,
         "days" : <Number of days from now into which events will be considered>,
         "full_day" : <if "True", registration declare people are present from 12AM to 11:59PM whatever the session date, if "False" uses event hours>,
         "time_zone" : <Time zone into which events shall be registered>
      }

   }

.. _`example`: conf/mail-pattern.txt
.. _`configuration file`: conf/conf.json

Secrets
-------

SMTP and IMAP server
********************

If not using gmail, you'll need the password of the smtp server your sending address uses to connect

API token
*********

Access to cloud API require authentication. Each time a user authenticate, it receives a token which is valid for a short period of time and
which gives access to a scope of API resources.
When using a CI/CD script, the user can't use the browser to authenticate. It shall be given a long term token, names "refresh token" which
is another way to authenticate without using the browser and create a new token.
The refresh token enabling access to the cloud API shall be provided in a json file

Depending on your use case, check either :

- The `Microsoft Token Generation`_
- The `Google Token Generation`_here

.. _`Microsoft Token Generation`: doc/microsoft-configuration.rst
.. _`Google Token Generation`: doc/google-configuration.rst

Usage
-----

In an environmentin which python, pip and bash has been installed :

.. code-block:: bash

   ./scripts/register.sh -a <Microsoft/Google> -k <My_TOKEN_FILE> -c <MY_CONF_FILE> -p <MY_SMTP__AND_IMAP_PASSWORD_IF_NEEDED> -t <RECIPIENT_ADDRESS> -f <SENDER_ADDRESS>

In an environemnt in which docker is available :

.. code-block:: bash

   ./scripts/launch.sh -a <Microsoft/Google> -k <My_TOKEN_FILE> -c <MY_CONF_FILE> -p <MY_SMTP__AND_IMAP_PASSWORD_IF_NEEDED> -t <RECIPIENT_ADDRESS> -f <SENDER_ADDRESS>

..code:bashrc



Testing
=======

Tested With
-----------

.. image:: https://img.shields.io/static/v1?label=python&message=3.12.6rc1&color=informational
   :target: https://www.python.org/
   :alt: Python
.. image:: https://img.shields.io/static/v1?label=robotframework&message=7.1&color=informational
   :target: http://robotframework.org/
   :alt: Robotframework

Environment
-----------

Tests can be executed in an environment :

* in which python, pip and bash has been installed, by executing the script `scripts/robot.sh`_, or

* in which docker is available, by using the `python image`_ in its latest version, which already contains python, pip and bash, by executing the script `scripts/test.sh`_

.. _`python image`: https://hub.docker.com/_/python/
.. _`scripts/robot.sh`: scripts/robot.sh
.. _`scripts/test.sh`: scripts/test.sh

Results
-------

The test results for latest release are here_

.. _here: https://MantaBots27318.github.io/sessions-management/report.html

Issues
======

.. image:: https://img.shields.io/github/issues/MantaBots27318/sessions-management.svg
   :target: https://github.com/MantaBots27318/sessions-management/issues
   :alt: Open issues
.. image:: https://img.shields.io/github/issues-closed/MantaBots27318/sessions-management.svg
   :target: https://github.com/MantaBots27318/sessions-management/issues
   :alt: Closed issues

Roadmap
=======

Contributing
============

.. image:: https://contrib.rocks/image?repo=MantaBots27318/sessions-management
   :alt: GitHub Contributors Image

Contact
=======

MantaBots - contact@mantabots.org