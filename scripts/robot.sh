#!/bin/bash
# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Script launching robotframework test
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# Retrieve absolute path to this script
script=$(readlink -f $0)
scriptpath=`dirname $script`

# Parse arguments from flags
args=""
key=""
while getopts s:l:d:k: flag
do
    case "${flag}" in
          s) args+=" --suite ${OPTARG}";;
          l) args+=" --loglevel ${OPTARG}";;
          d) args+=" --log ${OPTARG}/log.html --report ${OPTARG}/report.html";;
          k) key=${OPTARG}
    esac
done

# Create virtual environment
python3 -m venv /tmp/test
. /tmp/test/bin/activate

# Install required python packages
pip install --quiet --no-warn-script-location -r $scriptpath/../requirements-test.txt
pip install --quiet --no-warn-script-location -r $scriptpath/../requirements.txt

# Launch python scripts to test registration
python3 -m robot --variable data:$scriptpath/../test/data/                  \
                 $args                                                      \
                 $scriptpath/../test/cases


# Deactivate virtual environment
deactivate
rm -Rf /tmp/test/