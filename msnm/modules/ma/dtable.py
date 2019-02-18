# -*- coding: utf-8 -*-
"""
    :mod:`dtable`
    ===========================================================================
    :synopsis: Diaganosis routing table
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""
from msnm.modules.ma.drow import DRow
from msnm.exceptions.msnm_exception import DTableError

import logging

class DTable:
    '''    
    Implements the correspondence between variables and the IPs where they belong to.
    
    ====   =====  ======  =====
    ID     Vars    Type   IP
    ====   =====  ======  =====
    Q1     [list] R       192.168.1.50
    D1     [list] R       192.168.1.60
    ...    ...    ...     ...
    Localn [list] L       localhost
    ====   =====  ======  ===== 
    
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.__rows = {}
        
    def add_row(self,row_id, row):
        '''
        Add a row 
        
        '''
        
        method_name = "add_row()"
        
        if isinstance(row, DRow):
            self.__rows[row_id] = row
        else:
            raise DTableError(self,"This method only add rows of type DRow", method_name)
        
    def del_row(self,row_id):
        '''
        Delete a row 
        
        '''
        
        method_name = "del_row()"
        
        try:
            deleted_row = self.__rows.pop(row_id)            
        except KeyError:
            raise DTableError(self,"The row to be deleted has not been found", method_name)
        
        return deleted_row
    
    def get_row_by_id(self,row_id):
        '''
        Find a row by ID
        
        '''
        
        method_name = "find_row()"
        
        try:
            row = self.__rows[row_id]            
        except KeyError:
            raise DTableError(self,"The row has not been found", method_name)
        
        return row
    
    def get_row_by_var(self,var):
        '''
        Finding the row which var belongs to
        
        '''
        
        method_name = "get_row_by_var()"
        
        row = None
            
        for row_id in self.__rows.keys():
            row_vars = self.__rows[row_id].get_vars()
            if var in row_vars:
                row = self.__rows[row_id]
                logging.debug("Row %s contains the variable %s.",row_id, var)
                break
                        
        if not row: logging.warn("Variable %s does not belongs to any row :(",var)
        
        return row
    
    def get_number_rows(self):
        '''
        How many rows the table has?
        
        '''
                
        method_name = "get_number_rows()"

        return len(self.__rows)
    
    
    
    