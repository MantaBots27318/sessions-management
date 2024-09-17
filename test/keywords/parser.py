# -------------------------------------------------------
# Copyright (c) [2024] FASNY
# All rights reserved
# -------------------------------------------------------
""" Registration workflow keywords io functions """
# -------------------------------------------------------
# Nadège LEMPERIERE, @11th September 2024
# Latest revision: 11th September 2024
# -------------------------------------------------------

# System includes
from zoneinfo  import ZoneInfo
from json      import load
from os        import path


class Parser :
    """ Namespace for IO functions """

    # Results data
    s_ResultsFilename = path.normpath(path.join(path.dirname(__file__), '../data/results.json'))

    # Input data
    s_DataFilename = path.normpath(path.join(path.dirname(__file__), '../data/data.json'))

    def read_scenario(identifier, conf) :
        """ Read the scenario data """

        result = {}

        # Load input data
        with open(Parser.s_DataFilename, encoding="utf-8") as file: data = load(file)

        if not identifier in data : raise Exception('Data not found')

        result['data'] = data[identifier]
        result['conf'] = conf

        app_conf_path = path.normpath(path.join(path.dirname(__file__), '../../', conf))
        result['timezone'] = Parser.read_timezone(app_conf_path)

        return result

    def read_results(identifier, conf) :
        """ Read the scenario results """
        result = {}

        # Load scenario results
        with open(Parser.s_ResultsFilename, encoding="utf-8") as file: results = load(file)

        if not identifier in results : raise Exception('Result not found')

        result['data'] = results[identifier]
        result['data']['full'] = result['data']['full'].lower() == 'true'

        app_conf_path = path.normpath(path.join(path.dirname(__file__), '../../', conf))
        result['timezone'] = Parser.read_timezone(app_conf_path)

        return result

    def read_timezone(filename) :
        """ Read the timezone from the configuration file """
        result = None

        with open(filename, encoding="utf-8") as file:
            conf = load(file)
            if 'calendar' in conf and \
                'time_zone' in conf['calendar'] :
                result = ZoneInfo(conf['calendar']['time_zone'])

        return result
