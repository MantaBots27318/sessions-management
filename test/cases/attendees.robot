# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Registration test case to check registration attendees
# computation
# -------------------------------------------------------
# Nadège LEMPERIERE, @16th September 2024
# Latest revision: 16th September 2024
# -------------------------------------------------------

*** Settings ***
Documentation    A test suite for registration attendees computation scenarii
Library          ../keywords/workflow.py

*** Test Cases ***

1.1 Ensure Coaches And Students Are Correctly Managed
    ${scenario}      Load Scenario Data    3             test/data/conf_non_full.json
    ${reference}     Load Results          Attendees1    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
