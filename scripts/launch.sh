#!/bin/bash
# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Script launching process outside of CI/CD
# -------------------------------------------------------
# Nadège LEMPERIERE, @6th september 2024
# Latest revision: 6th september 2024
# -------------------------------------------------------

# Retrieve absolute path to this script
script=$(readlink -f $0)
scriptpath=`dirname $script`

# Use python docker to launch registration
docker run -it --rm \
       --entrypoint /bin/bash \
       -v $scriptpath/../:/home \
       python:latest \
       /home/scripts/register.sh $@
