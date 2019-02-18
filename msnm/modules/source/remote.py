# -*- coding: utf-8 -*-
"""
    :mod:`remote`
    ===========================================================================
    :synopsis: Common functionality for remote sources
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""
from msnm.modules.source.source import Source

class RemoteSource(Source):
    
    def __init__(self):
        super(RemoteSource, self).__init__()
        self._type = Source.TYPE_R