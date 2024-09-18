# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Registration test case to check registration attendees
# computation using Google
# -------------------------------------------------------
# Nadège LEMPERIERE, @16th September 2024
# Latest revision: 16th September 2024
# -------------------------------------------------------

*** Settings ***
Documentation    A test suite for registration attendees computation scenarii using Google
Library          ../keywords/workflow.py

*** Test Cases ***

1.1.1 Ensure Registration Of Event With Adults And Students
    ${scenario}      Load Scenario Data    3             test/data/conf_non_full.json    Google
    ${reference}     Load Results          Attendees1    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com  test@test.org
    Check Final State        ${reference}    ${result}

1.1.2 Ensure Non Registration Of Event With No Attendees
    ${scenario}      Load Scenario Data    9             test/data/conf_non_full.json    Google
    ${reference}     Load Results          Nothing       test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com  test@test.org
    Check Final State        ${reference}    ${result}

1.1.3 Ensure Non Registration Of Updated Event With No Attendees Change
    ${scenario}      Load Scenario Data    3             test/data/conf_non_full.json    Google
    ${reference}     Load Results          Attendees1    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com  test@test.org
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${reference}     Load Results          Nothing       test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

1.1.4 Ensure Registration Of Updated Event With Only Attendees Change
    ${scenario}      Load Scenario Data    3             test/data/conf_non_full.json    Google
    ${reference}     Load Results          Attendees1    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com  test@test.org
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    10            test/data/conf_non_full.json    Google
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Attendees2    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

1.1.5 Ensure No Registration Of Updated Event With Less Attendees
    ${scenario}      Load Scenario Data    3             test/data/conf_non_full.json    Google
    ${reference}     Load Results          Attendees1    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    12            test/data/conf_non_full.json    Google
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Nothing       test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

