======================================
Privacy Policy For sessions-management
======================================


Last updated: 09/27/2024

Introduction
============

sessions-management is an application designed to automate email sending for robotics team sessions, access calendar events, and use contact lists. This app is used solely within a private CI/CD pipeline on GitHub and is not distributed publicly. We are committed to protecting your privacy and ensuring that any personal data we handle is secure. This policy outlines how we manage user data and your rights regarding that data.

Data Collection and Use
=======================

- **OAuth2 Authentication**: We use Google’s OAuth2 system to access data from the Google Calendar API, Gmail API, and Google Contacts API. The OAuth2 token is securely stored in GitHub Secrets as part of our `CI/CD pipeline`_

.. _`CI/CD pipeline`: https://github.com/MantaBots27318/sessions-management/blob/main/.github/workflows/register-sharkbots.yml

- **Data We Access**:

  * **Calendar Events**: The app accesses calendar events to retrieve information about upcoming robotics team sessions for the purpose of sending email notification to our premises owner.

  * **Emails**: The app accesses Gmail to automate the sending of email notifications for scheduled sessions.

  * **Contacts List**: The app accesses the Google Contacts API to retrieve information on the attendees names and tags.
  
- **Purpose of Data Use**: The data accessed is strictly used for email automation related to robotics team session notifications and event coordination. It is not used for any other purposes, nor is it shared with any third parties.

Data Security
=============

- **Storage of Credentials**: OAuth tokens are stored securely in GitHub Secrets, which are encrypted and only accessible by the CI/CD pipeline.

- **Restricted Permissions**: The app only requests the minimum necessary permissions to function (accessing calendar events, emails, and contact lists), operating under the principle of least privilege.

- **Data Sharing**: We do not share any user data with third parties. The data accessed by the app is used solely for internal purposes within the robotics team and in the specific CI/CD pipeline.

- **Commitment to Non-Distribution**: This app is not publicly distributed or shared. It is used exclusively in the private CI/CD pipeline for the purpose of managing and automating email notifications for robotics team events. The OAuth2 secret token is securely stored and will not be exposed or used in any public or shared environment.

User Control and Rights
=======================

- **Access to Data**: Only the app creator and authorized users within the CI/CD pipeline can access the OAuth token and use the app.

- **Revoking Access**: You can revoke the app’s access to your Google account at any time by removing the app from your Google account, preventing further data access or use.

Data Retention
==============

- **Retention of OAuth Tokens**: refresh tokens are stored securely in the CI/CD environment and are retained only as long as necessary to execute the app’s functions. Tokens will be refreshed periodically as needed by the pipeline and deleted when no longer required.

Changes to This Policy
======================

We may update this privacy policy from time to time. You are encouraged to review this policy periodically for any changes. Continued use of the app after modifications will constitute your acknowledgment of the updated policy.

Contact Us
==========

If you have any questions or concerns about this privacy policy or the app’s data usage, please contact us at: coaches@mantabots.org