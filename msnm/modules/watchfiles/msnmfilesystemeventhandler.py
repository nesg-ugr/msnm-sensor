# -*- coding: utf-8 -*-

"""
    :mod:`MSNMFileSystemEventHandler Module`
    ===========================================================================
    :synopsis: Watch for changes in the netflow (nfcapd) directory. 
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

from watchdog.events import FileSystemEventHandler
from fcparser import fcparser
from msnm.modules.source.iptables import IPTables
from msnm.modules.config.configure import Configure
import pandas as pd
import numpy as np
from subprocess import call
from datetime import datetime
import time
import sys
import os
import logging
from msnm.exceptions.msnm_exception import MSNMError, DataSourceError,\
    SensorError

class MSNMFileSystemEventHandler(FileSystemEventHandler):
    """
    Class that listen for changes in netflow output folder. In this case, when a new
    nfcapd file is generated, an event is raised. Such an event start the whole MSNM
    sensor procedure: 
        1.- Get the data from several sources. Right now netflow and iptables logs are considered.
        2.- Parse data sources (flow parser) to make a new observation.
        3.- Monitoring the new observation. Compute Q and D statistics
        4.- Diagnosis, if needed (oMEDA)
        
    Attributes
    ----------
    _sensor : msnm.Sensor
        Class representing the MSNM sensor
    _iptables : msnm.source.IPTables
        IPTables log parser.
    _variables : list
        All variables name considered
        
    See Also
    --------
    msnm.sensor
    msnm.source.IPTables
    msnm.utils
    numpy
    pandas
    
    """

    def __init__(self, sensor, variables):        
        self._sensor = sensor
        self._iptables = IPTables()
        self._variables = variables
        
    def on_created(self, event):
        """        
            Called when a new file is created in the nfcapd output folder
        """
        super(MSNMFileSystemEventHandler, self).on_created(event)
        
    def on_moved(self, event):
        """        
            Called when a new file is renamed in the nfcapd output folder.
            This method is in charge of launch all sensor tasks which are mentioned
            in this class description
        """
        super(MSNMFileSystemEventHandler, self).on_moved(event)
        
        try:
        
            ts = datetime.strftime(datetime.now(),'%Y%m%d_%H%M%S')
            
            # Get *.csv from nfcapd file 
            self.run_nfdump(event.dest_path)
            start_time = time.time()
            # Get *.csv from iptables.log file
            self.run_iptables_parser(ts)
            elapsed_time = time.time() - start_time
            print "Elapsed time in iptables parsing -> " + str(int(elapsed_time)) + " s"
            # Launch parser
            self.launch_parsing()        
            
            # Monitoring
            test = self.launch_monitoring()
            # If an anomaly is detected -> launch diagnosis
            self.launch_diagnosis(test)        
            
            # Backup files
            os.rename("./data_raw/netflow-12345.csv", "./data_raw_backup/netflow-12345_" + ts + ".csv")
            os.rename("./data_raw/iptables-12345.csv", "./data_raw_backup/iptables-12345_" + ts + ".csv")                
            os.rename("./data_output/output-12345.dat", "./data_output_backup/output-12345_" + ts + ".dat")
            list_splitted = event.dest_path.split('/')
            nfcapd_file_name = list_splitted[len(list_splitted) - 1]
            os.rename(event.dest_path,"./data_raw_backup/" + nfcapd_file_name + "_" + ts)
        
        except DataSourceError as edse:
            logging.warn("Some datasource parsing has been failed, skipping ... ERROR: %s",edse.get_msg())       
        except MSNMError as emsnme:
            emsnme.print_error()
            exit(1)
                
        # Remove *.csv last observation rar files     
        #os.remove(self._netflow_dumps_path)
        #os.remove(self._iptables_dumps_path)
        
    def run_nfdump(self,file_path):
        """
        From a new netflow file, it is in charge of to call nfdump to transform the byte based
        netflow files to a *.csv file as input of the flow parser.
            
        Raises
        ------
        MSNMError
        
        """
                
        method_name = "run_nfdump()"      
        
        # Netflow source files
        config = Configure()
        netflow_dumps_path = config.get_config()['DataSources']['Netflow']['dumps'] #*.csv        
       
            
        print " "
        print "NEW nfcapd file generated at " + time.ctime(time.time())
                        
        # Call to nfdump process.
        retcode = call("nfdump -r " + str(file_path) + " -q -o csv >> " + netflow_dumps_path,shell=True)
            
        if retcode != 0: 
            raise MSNMError(self,"Error calling nfdump", method_name)
        
        logging.info("New nfdump csv generated: %s",netflow_dumps_path)
      
        try:
            # add new id column to merge in parser
            # TODO: build a more elaborated method to do this e.g., from a dateframe utils package
            df = pd.read_csv(netflow_dumps_path,header=None, index_col=0)
            df.loc[:,df.shape[1]] = range(100000, 100000 + df.shape[0])
            df.to_csv(netflow_dumps_path, encoding='utf-8', header=False)
                        
        except ValueError:
            # FIXME: Sometimes nfcapd generates an empyt file :( I do not why :(
            logging.warn("Nfdump file is empty, skipping ... ERROR: %s ",sys.exc_info()[0])
            raise DataSourceError(self,"Nfdump file is empty ....", method_name)

        except Exception:
            raise MSNMError(self,sys.exc_info()[0], method_name)        
            
    def run_iptables_parser(self,ts):
        """
        Gets the iptables.log files, parse the n ``linesToParse`` last lines of it. After that, this set of lines
        are filtered according to the time stamp obtained from the master source, i.e., netflow
        
        Raises
        ------
        MSNMError       
        
        """
        
        method_name = "run_iptables_parser()"
        
        # Get configuration
        config = Configure()
        netflow_dumps_path = config.get_config()['DataSources']['Netflow']['dumps'] #*.csv
        
        # IPTables source files
        iptables_captures_path = config.get_config()['DataSources']['IPTables']['captures']; # *.log files
        iptables_backups_path = config.get_config()['DataSources']['IPTables']['backups']; # *.log backups
        iptables_dumps_path = config.get_config()['DataSources']['IPTables']['dumps']; # *.cs
        iptables_n_last_lines = config.get_config()['DataSources']['IPTables']['linesToParse']; # n last lines of iptables.log to parse
                        
        # Path for the backup
        iptables_backup_log = iptables_backups_path + "/iptables_" + ts + ".log"
        
        print " "
        print "Getting iptables.log file and parsing it --> " + iptables_backup_log
        
        try:
        
            # Get the n last lines of the /var/log/iptables and save it in the backup dir to be parsed
            self._iptables.get_file_to_parse(iptables_captures_path, iptables_backup_log, iptables_n_last_lines)                    
            
            # Get lines from the last file which match with the same time interval as in the current netflow dump
            self._iptables.parse(iptables_backup_log, iptables_dumps_path, netflow_dumps_path=netflow_dumps_path)
        except DataSourceError as dse:
            raise dse

        
    def launch_monitoring(self):
        """
        Once the parsing (flow parser) procedure is done, this method is in charge of to start the monitoring
        process
        
        Raises
        ------
        MSNMError
        
        """
        
        method_name = "launch_monitoring()"
        
        # Get configuration parmas
        config = Configure()
        parser_output_path = config.get_config()['ParserEngine']['output']; # Parser output (*.dat) that is the input of the sensor for monitoring
        
        try:
            test = np.loadtxt(parser_output_path, comments="#", delimiter=",", skiprows=1, usecols=range(1,len(self._variables) + 1))
            test = test.reshape((1,test.size))
            self._sensor.do_monitoring(test)
        except SensorError as ese:
            raise MSNMError(self, ese.msg,method_name)
        except MSNMError as emsnme:
            raise emsnme
        
        
        print " "
        print "############### MONITORING ################"
        print "UCLd --> %f" % self._sensor.get_model().get_mspc().getUCLD()
        print "Dst --> %f" %self._sensor.get_mspc().getDst()
        print "UCLq --> %f" % self._sensor.get_model().get_mspc().getUCLQ()
        print "Qst --> % f" % self._sensor.get_mspc().getQst()
        
        return test
        
    def launch_parsing(self):
        
        """
        Launch the parsing procedure (flow parser)
        
        Raises
        ------
        MSNMError
        
        """
        
        method_name = "launch_parsing()"
        
        # Parser configuration options        
        config = Configure()
        parser_config_file = config.get_config()['ParserEngine']['config']; # Parser configuration file 
        
        print " "
        print "############### PARSING ################"   
        
        #TODO: modify parser source to raise ParseError or some like that as in the MSNM sensor.
                     
        try:
            fcparser.main(parser_config_file)
        except Exception:
            raise MSNMError(self,sys.exc_info()[0],method_name) 
        
    def launch_diagnosis(self, test):
        
        """
        Once an anomaly is detect, this method runs the diagnosis of the observation under study.
        
        Raises
        ------
        MSNMError
        
        """
        
        method_name = "launch_diagnosis()"
        
        try:
            # Check if the observation is anomalous and compute oMEDA then
            if self._sensor.get_mspc().getDst() > self._sensor.get_model().get_mspc().getUCLD()  or self._sensor.get_mspc().getQst() > self._sensor.get_model().get_mspc().getUCLQ() :
                print "Anomaly detected!"
                dummy = np.ones((1,1)) 
                self._sensor.do_diagnosis(test,dummy)
        except SensorError as ese:
            raise MSNMError(self, ese.msg,method_name)
        except MSNMError as emsnme:
            raise emsnme
        
        
        
        

                
        
        
        
        
        