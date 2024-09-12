#!/bin/bash
# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
# Script launching testing outside of CI/CD
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th september 2024
# Latest revision: 11th september 2024
# -------------------------------------------------------


# Retrieve absolute path to this script
script=$(readlink -f $0)
scriptpath=`dirname $script`

# Use python docker to launch registration
docker run -it --rm \
       --entrypoint /bin/bash \
       -v $scriptpath/../:/home \
       --workdir /home \
       python:latest \
       /home/scripts/robot.sh $@