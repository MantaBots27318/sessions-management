=======================
microsoft-configuration
=======================

Prerequisites
=============

An Azure subscription shall have been created for the personal account owning the contact list

Setting up the Azure Application To Access Personal Account Data
================================================================

Creating The Azure app
---------------------

1. Go to Microsoft Entra ID > Manage > App registrations
2. Create a new App registration and choose its name
3. Choose to support **Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)**. This is key to make sure that your app will gain access to the user personal account which is located in another Azure tenant and it can not be change afterwards
4. Set the redirect URI to https://mantabots.org
5. Create the app

Configuring the app
-------------------

1. Go to Authentication. Add a new web platform and choose to implicit grant shall be set to Access tokens and ID tokens

.. image:: azure-app-authentication.png


2. Go to Api permissions and grant the following API permissions :
   * offline_access enables to maintain the acquired authorization the app has for the Microsoft personal account
   * User.Read enables to get personal account information
   * Calendars.ReadWrite enables to get calendar events and update them with registration date
   * Contacts.Read enables to get contact list
   * Mail.Send enables to send email

.. image:: azure-app-api-permissions.png


3. Go to Certificates and secrets and create a secret. Store it in a safe place:


.. image:: azure-app-secret.png


Retrieving API access credentials
=================================

Format
------

.. code-block:: JSON

   {
      "token": <authorized oauth user short term token - will be refreshed if no longer valid>,
      "refresh_token": <authorized oauth user long term refresh token>,
      "token_uri": "https://login.microsoftonline.com/common",
      "client_id": <MY_AZURE_APP_ID>,
      "client_secret": <MY_AZURE_APP_SECRET>,
      "tenant_id": "9188040d-6c67-4c5b-b112-36a304b66dad",
      "scopes": ["Contacts.Read", "Calendars.ReadWrite", "Mail.Send", "User.Read"]
   }

N.B : The tenant_id is the default value for personal accounts, not the one from the organizational account in which the app has been created

Content
-------

The token and refresh token value can be gathered the following way :

- In a web browser, enter address :
.. code-block:: bash

   https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=<MY CLIENT ID>&response_type=code&redirect_uri=https://mantabots.org&response_mode=query&scope=offline_access%20Contacts.Read%20Calendars.ReadWrite%20Mail.Send%20User.Read

- Select the user owning the calendar and the contact list for authentication
- You'll be redirected to

.. code-block:: bash
   https://mantabots.org/?code=<AUTHORIZATION CODE>

- In the command line, use curl :

.. code-block:: bash

   curl -X POST https://login.microsoftonline.com/common/oauth2/v2.0/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=<MY_CLIENT_ID>" \
     -d "scope=offline_access Contacts.Read Calendars.ReadWrite Mail.Send User.Read" \
     -d "code=<AUTHORIZATION CODE>" \
     -d "redirect_uri=https://mantabots.org" \
     -d "grant_type=authorization_code" \
     -d "client_secret=<MY_CLIENT_SECRET>"

The result will contain a short term token and a long term token to update the token.json file

Setting up the Outlook Calendar trigger
=======================================

Creating the trigger
--------------------

1. Log onto the Microsoft 365 personal account owning the calendar

.. _`Google Apps Scripts`: https://script.google.com/home?pli=1

Connecting to the Github CI/CD script
-------------------------------------
