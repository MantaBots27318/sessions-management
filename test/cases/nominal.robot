# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Registration test case """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

*** Settings ***
Documentation    A test suite for nominal registration scenarii
Library          ../keywords/workflow.py

*** Test Cases ***
1.1 Ensure Registration Of 1 New Full Day Event With Full Day Conf Using Smtp Server
    ${scenario}      Build Scenario Data    Nominal1
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

1.2 Ensure Registration Of 1 New Full Day Event With Non Full Day Conf Using Smtp Server
    ${scenario}      Build Scenario Data    Nominal2
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

1.3 Ensure Registration Of 1 New Non Full Day Event With Full Day Conf Using Smtp Server
    ${scenario}      Build Scenario Data    Nominal3
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

1.4 Ensure Registration Of 1 New Non Full Day Event With Non Full Day Conf Using Smtp Server
    ${scenario}      Build Scenario Data    Nominal4
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

2.1 Ensure Coaches And Students Are Correctly Managed
    ${scenario}      Build Scenario Data    Nominal5
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

3.1 Ensure Events Selection Is Correctly Managed For Non Full Day Data
    ${scenario}      Build Scenario Data    Nominal6
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

3.2 Ensure Events Selection Is Correctly Managed For Full Day Data
    ${scenario}      Build Scenario Data    Nominal7
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}

4.1 Ensure Already Registered Events Are Not Sent Back
    ${scenario}      Build Scenario Data    Nominal7
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    ${scenario}      Build Scenario Data    Nominal8
    Check Final State        ${scenario}    ${result}

4.2 Ensure Updated Or New Events Are Sent
    ${scenario}      Build Scenario Data    Nominal7
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}
    ${scenario2}     Build Scenario Data    Nominal9
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    ${scenario}      Build Scenario Data    Nominal8
    Check Final State        ${scenario}    ${result}

5.1 Ensure Registration Is Only For Items Containing Topic
    ${scenario}      Build Scenario Data    Nominal10
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${scenario}    ${result}
