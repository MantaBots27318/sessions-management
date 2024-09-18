# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Registration test case to check registration events
# filtering
# -------------------------------------------------------
# Nadège LEMPERIERE, @16th September 2024
# Latest revision: 16th September 2024
# -------------------------------------------------------

*** Settings ***
Documentation     A test suite for events filtering
Library          ../keywords/workflow.py

*** Test Cases ***

2.1.1 Ensure Events Filtering On Date Is Correctly Managed For Non Full Day Data
    ${scenario}      Load Scenario Data    4        test/data/conf_30.json          Google
    ${reference}     Load Results          Events1  test/data/conf_30.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

2.1.2 Ensure Events Filtering On Date Is Correctly Managed For Full Day Data
    ${scenario}      Load Scenario Data    5        test/data/conf_30.json          Google
    ${reference}     Load Results          Events2  test/data/conf_30.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

2.1.3 Ensure Events Filtering On Topic Is Correctly Managed For Full Day Data
    ${scenario}      Load Scenario Data    7        test/data/conf_non_full.json    Google
    ${reference}     Load Results          Events3    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

2.1.4 Ensure Events Filtering On Status Is Correctly Managed For Full Day Data
    ${scenario}      Load Scenario Data    13        test/data/conf_non_full.json    Google
    ${reference}     Load Results          Nothing   test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
