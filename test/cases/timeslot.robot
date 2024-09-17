# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Registration test case to check registration timeslot
# computation
# -------------------------------------------------------
# Nadege LEMPERIERE, @16th September 2024
# Latest revision: 16th September 2024
# -------------------------------------------------------

*** Settings ***
Documentation    A test suite for registration timeslot computation scenarii
Library          ../keywords/workflow.py

*** Test Cases ***
3.1 Ensure Registration Of 1 New Full Day Event With Full Day Conf
    ${scenario}      Load Scenario Data    1            test/data/conf_full.json
    ${reference}     Load Results          Timeslot1    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.2 Ensure Registration Of 1 New Full Day Event With Non Full Day Conf
    ${scenario}      Load Scenario Data    1            test/data/conf_non_full.json
    ${reference}     Load Results          Timeslot2    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.3 Ensure Registration Of 1 New Non Full Day Event With Full Day Conf
    ${scenario}      Load Scenario Data    2            test/data/conf_full.json
    ${reference}     Load Results          Timeslot3    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.4 Ensure Registration Of 1 New Non Full Day Event With Non Full Day Conf
    ${scenario}      Load Scenario Data    2            test/data/conf_non_full.json
    ${reference}     Load Results          Timeslot4    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.5 Ensure Non Registration Of 1 Already Registered Full Day Event With Full Day Conf
    ${scenario}      Load Scenario Data    1            test/data/conf_full.json
    ${reference}     Load Results          Timeslot1    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${reference}     Load Results          Nothing      test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.6 Ensure Non Registration Of 1 Already Registered Full Day Event With Non Full Day Conf
    ${scenario}      Load Scenario Data    1            test/data/conf_non_full.json
    ${reference}     Load Results          Timeslot2    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${reference}     Load Results          Nothing      test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.7 Ensure Non Registration Of 1 Already Registered Non Full Day Event With Full Day Conf
    ${scenario}      Load Scenario Data    2            test/data/conf_full.json
    ${reference}     Load Results          Timeslot3    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${reference}     Load Results          Nothing      test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.8 Ensure Non Registration Of 1 Already Registered Non Full Day Event With Non Full Day Conf
    ${scenario}      Load Scenario Data    2            test/data/conf_non_full.json
    ${reference}     Load Results          Timeslot4    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${reference}     Load Results          Nothing      test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.9 Ensure Registration Of 1 Updated Non Full Day Event With None Full Day Conf Using Smtp Server
    ${scenario}      Load Scenario Data    2            test/data/conf_non_full.json
    ${reference}     Load Results          Timeslot4    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    1            test/data/conf_non_full.json
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Timeslot1    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.10 Ensure Non Registration Of 1 Updated Non Full Day Event With None Full Day Conf Using Smtp Server When Update Decrease Timeslot
    ${scenario}      Load Scenario Data    2            test/data/conf_non_full.json
    ${reference}     Load Results          Timeslot4    test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    11           test/data/conf_non_full.json
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Nothing      test/data/conf_non_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.11 Ensure Non Registration Of 1 Updated Non Full Day Event With Full Day Conf Using Smtp Server When Update Is The Same Day
    ${scenario}      Load Scenario Data    2            test/data/conf_full.json
    ${reference}     Load Results          Timeslot3    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    1            test/data/conf_full.json
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Nothing      test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.12 Ensure Non Registration Of 1 Updated Non Full Day Event With Full Day Conf Using Smtp Server When Update Decrease Timeslot
    ${scenario}      Load Scenario Data    2            test/data/conf_full.json
    ${reference}     Load Results          Timeslot3    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    11           test/data/conf_full.json
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Nothing    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}

3.13 Ensure Registration Of 1 Updated Non Full Day Event With Full Day Conf Using Smtp Server When Update Is The Other Day
    ${scenario}      Load Scenario Data    2            test/data/conf_full.json
    ${reference}     Load Results          Timeslot3    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}
    ${scenario}      Update Scenario Data From Results   ${scenario}    ${result}
    ${scenario2}     Load Scenario Data    8            test/data/conf_full.json
    ${scenario}      Merge Scenario Data                 ${scenario}    ${scenario2}
    ${reference}     Load Results          Timeslot5    test/data/conf_full.json
    ${result}        Run Registration Workflow with Mocks    ${scenario}    moi@moi.com    test@test.org
    Check Final State        ${reference}    ${result}



