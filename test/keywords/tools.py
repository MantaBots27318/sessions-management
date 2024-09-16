# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Registration workflow keywords tools """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# System includes
from zoneinfo  import ZoneInfo
from json      import load

class Tools :
    """ Namespace for tools """

    def read_timezone(filename) :
        """ Read the timezone from the configuration file """
        result = None

        with open(filename, encoding="utf-8") as file:
            conf = load(file)
            if 'calendar' in conf and \
                'time_zone' in conf['calendar'] :
                result = ZoneInfo(conf['calendar']['time_zone'])

        return result