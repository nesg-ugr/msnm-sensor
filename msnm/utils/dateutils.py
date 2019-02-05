# -*- coding: utf-8 -*-
"""
    :mod:`Date utilities`
    ===========================================================================
    :synopsis: Several methods to play with dates
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

from datetime import datetime
from msnm.modules.config.configure import Configure

def get_timestamp():
    """
    Gets the current time within a specific format found in ``config/sensor.yaml``
        
    Return
    ------
    ts:
        Current time stamp with specific format as shown in the configuration file (sensor.yaml)
    """
    config = Configure()
    tstsDateFormat = config.get_config()['GeneralParams']['tsDateFormat']
    
    return datetime.strftime(datetime.now(),tstsDateFormat)
