# -*- coding: utf-8 -*-
"""
    :mod:`drow`
    ===========================================================================
    :synopsis: A row in the diagnosis routing table
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

class DRow():
    '''
    A row in the diagnostic table
    '''
    
    # List of the belonging variables of a certain source
    __VARS = 'vars'
    # Type of the source: remote (R) or local (L)
    __TYPE = 'type'
    # IP of where the source comes from: 'localhost' means the source is local
    __IP = 'ip'


    def __init__(self, list_of_vars, source_type, ip):
        '''
        Constructor
        '''
        self._row = {self.__VARS:list_of_vars}        
        self._row = {self.__TYPE:source_type}
        self._row = {self.__IP:ip}
        
    def __str__(self):
        toPrint = self.__VARS + ":" + self._rows
        
    def get_vars(self):
        return self._row[self.__VARS]
        
    def get_type(self):
        return self._row[self.__TYPE]
    
    def get_ip(self):
        return self._row[self.__IP]