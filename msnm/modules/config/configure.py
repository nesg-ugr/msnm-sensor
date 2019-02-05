# -*- coding: utf-8 -*-

"""
    :mod:`Configuration utilities module`
    ===========================================================================
    :synopsis: Configuration
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

import yaml
from msnm.exceptions.msnm_exception import ConfigError
import sys
import traceback

class Configure(object):
    """ 
        Class containing the configuration file parameters located in ``config/sensor.yaml``. There is just one instance of this class (singleton) that 
        can be used from anywhere. 
    
    """        
    __CONFIG_FILE_PATH = ''
    
    # Just one instance
    __instance = None
    
    # Contains all the parameters of the sensor configuration file
    config_params = {}
    
    # singleton pattern
    def __new__(cls):
        if Configure.__instance is None:
            Configure.__instance = object.__new__(cls)
        return Configure.__instance
    
    def load_config(self, config_file):
        """
        Load the MSNM sensor configuration parameters from ``config/sensor.yaml`` file. 
        It should be called at sensor starting time.
            
        """
        
        method_name = "load_config()"
        
        self.__CONFIG_FILE_PATH = config_file
        
        # Get the general configuration file
        Configure.__instance.config_params = self.__load_yaml_file(config_file)
        
        # Load flow parser configuration files for each local source
        src_local = Configure.__instance.config_params['DataSources']
        
        # Having a local sources means that they must be parsed to build the complete observation. This way, we have to load the flowParser configuration file/s
        if 'local' in src_local.keys():
            # Every local source has its own parser configuration file
            for i in Configure.__instance.config_params['DataSources']['local']:               
                
                # data source configuration file
                path_to_config_file = Configure.__instance.config_params['DataSources']['local'][i]['parserContents'] 
                flow_parser_content_config = self.__load_yaml_file(path_to_config_file)
                Configure.__instance.config_params['DataSources']['local'][i]['parserContents'] = flow_parser_content_config
            
            
    def __load_yaml_file(self, path_to_file):
        """
        Read and load the main configuration *.yaml file
        
        Parameters
        ----------
        path_to_file: str
            Path to the configuration file
            
        Return
        ------
        conf: dict
            Dictionary containing all the configuration parameters
            
        Raise
        -----
        ConfigError
            When the configuration files does not exits or there is something wrong formatted or illegal in the the *.yaml file
                     
        """
                
        method_name = "load_yaml_file()"
        
        try:        
            stream = file(path_to_file, 'r')
            conf = yaml.load(stream)
            stream.close()
        except yaml.scanner.ScannerError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback ,limit=5, file=sys.stdout)
            raise ConfigError(self,"Incorrect config file '%s'" %(self.get_config_path()),method_name)
        except Exception:
            raise ConfigError(self,sys.exc_info()[1],method_name)
        
        return conf
        
        
    def get_config(self):
        """
        Get the configuration parameters. To be used for accessing to whichever the configuration parameter.
        
        Return
        ------
        config_params: dict
            Dictionary containing all the configuration parameters
            
        Example
        -------
        # Get configuration
        config = Configure()
        # Get the desired configuration parameter. In this case a scheduling timer.
        timer = config.get_config()['GeneralParams']['dataSourcesScheduling']
        """
        return Configure.__instance.config_params
    
    def get_config_path(self):
        """
        Get the configuration file path
        
        Return
        ------
        path: str
            File configuration file system location
            
        """
        return self.__CONFIG_FILE_PATH
    
    
    
        