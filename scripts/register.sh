#!/bin/bash
# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Script installing and executing registration
# -------------------------------------------------------
# Nadège LEMPERIERE, @6th september 2024
# Latest revision: 6th september 2024
# -------------------------------------------------------

# Retrieve absolute path to this script
script=$(readlink -f $0)
scriptpath=`dirname $script`

# Parse arguments from flags
args=""
while getopts c:p:t:f:k:a flag
do
    case "${flag}" in
          k) args+=" --token ${OPTARG}";;
          c) args+=" --conf ${OPTARG}";;
          p) args+=" --mail ${OPTARG}";;
          t) args+=" --receiver ${OPTARG}";;
          f) args+=" --sender ${OPTARG}";;
          a) args+=" --api ${OPTARG}";;
    esac
done

echo ${OPTARG}


# Create virtual environment
python3 -m venv /tmp/register
. /tmp/register/bin/activate

# Install required python packages
pip install --quiet -r $scriptpath/../requirements.txt

# Launch registration process
python3 $scriptpath/../manager.py run $args

# Deactivate virtual environment
deactivate
rm -Rf /tmp/register/

