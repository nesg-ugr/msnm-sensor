# -*- coding: utf-8 -*-
"""
    :mod:`Sensor offline mode utilities and support`
    ===========================================================================
    :synopsis: Several classes and methods for supporting offline sensor functionality
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

import sys, os
import shutil
import numpy as np
import pandas as pd
import logging

from time import sleep
from dateutil import parser
from msnm.utils import dateutils

from msnm.modules.thread.thread import MSNMThread
from msnm.modules.config.configure import Configure

class OfflineThread(MSNMThread):
    '''
    Implements MSNM sensor static functionality when parsed files are externally provided i.e., they are not generated online.
    
    TODO: to be completed and tested 
    '''
    
    def __init__(self):
        super(OfflineThread,self).__init__()
        
    def run(self):
        # Get configuration
        config = Configure()
        
        # Load local data sources running in static Mode
        local_dict = {}        
        try:
            src_local = config.get_config()['DataSources']['local']
                
            logging.debug("Loading %s local sources %s.",len(src_local),src_local.keys())
                
            for i in src_local.keys():
                
                if src_local[i]['staticMode']:
                    
                    logging.debug("Local source %s is running in static mode.",i)                        
                    local_dict[i] = src_local[i]
                    
        except KeyError as ke:
            logging.warning("There are no local sources configured: %s", ke)
        
        
        #Test observations per source
        obsBySource = {}
        
        # Get external files
        for i in local_dict.keys():
            if i == 'Netflow':
                # Get all parsed *.dat files from a specific folder
                staticFiles = local_dict[i]['staticParsedFilesPath']
                
                # Get the name of the files ordered
                filesOrdered = np.sort(os.listdir(staticFiles))
                
                logging.debug("Got %s files from source %s ",len(filesOrdered),i)
                
                # Remove auxiliar files weights.dat and stats.log
                filesOrdered = filesOrdered[np.logical_not('stats.log' == filesOrdered)]
                filesOrdered = filesOrdered[np.logical_not('weights.dat' == filesOrdered)]
                
                logging.debug("Removed unuseless files from source %s. Total files to process: %s ",i,len(filesOrdered))
                
                # Generate a dataframe containing all *.dat (all observations)
                # Date range as index
                dstart = filesOrdered[0][7:][0:-4]# get initial timestamp from the first file name, e.g., output-20160209t1249.dat            
                dend = filesOrdered[-1][7:][0:-4]# get ending timestamp from the first file name, e.g., output-20160209t1249.dat
                d_range = pd.date_range(dstart,dend,freq='1min')
                dfAllObs = pd.DataFrame(filesOrdered,d_range,columns=['obs'])
                
                logging.debug("Got all obs from %s to %s",dstart,dend)
                
                # Get the test date range
                date_range_start = local_dict[i]['staticObsRangeStart']
                date_range_end = local_dict[i]['staticObsRangeEnd']
                obsBySource[i] = dfAllObs[date_range_start:date_range_end]
                            
                logging.debug("%s observations filtered from %s to %s",len(obsBySource[i]),date_range_start,date_range_end)
                
            else:
                logging.debug("TODO: managing %s local sources",i)
                
        
        # dataSourcesScheduling
        schedulingTimer = config.get_config()['GeneralParams']['dataSourcesScheduling']
        nfcapdTimeFormat = config.get_config()['GeneralParams']['dateFormatNfcapdFiles']
        netflow_parsed_folder = config.get_config()['DataSources']['local']['Netflow']['parsed']
        netflow_dat_manual_folder = config.get_config()['DataSources']['local']['Netflow']['staticParsedFilesPath']
        netflow_captures = config.get_config()['DataSources']['local']['Netflow']['captures']
    
        
        # flag to finish the simulation
        end = False
        
        # Observations counter
        obsCounter = 0
        
        # list of observations
        obsList = list(obsBySource['Netflow']['obs'])
        
        while not end and not self._stopped_event.isSet():
            
            try:
                # Process the observation
                obsToProcess = obsList[obsCounter]
                
                logging.debug("Observation to process: %s",obsToProcess)
                
                # ts from obs file
                tsFile = obsToProcess[7:][0:-4]
                
                # ts from the current host
                ts = dateutils.get_timestamp()
                
                # TODO ts for nfcap file 
                tsdatetime = parser.parse(ts)
                tsdatetimeFile = parser.parse(tsFile)
                tsFormatted = tsdatetime.strftime(nfcapdTimeFormat)
                tsFormattedFile = tsdatetimeFile.strftime(nfcapdTimeFormat)
                
                logging.debug("Creating nfcapd.current.%s", tsFormatted)               
                            
                # Generate nfcapd synthetic current filefile with equal timestamp as the observation
                nfcapdCurrent = netflow_captures + os.sep + "nfcapd.current." + tsFormatted            
                with open(nfcapdCurrent,'w') as f:
                    f.write("Dummy nfcapd for static mode current ")
                
                # Move current nfcapd file to emulate on_moved event in netflow source
                #In static mode the emulated nfcapd files has the name like  nfcapd.201701302000_2016001182312, where last ts after '_' is the ts of the statid *.dat
                # file                 
                nfcapdDummy = netflow_captures + os.sep + "nfcapd." + tsFormatted  + "_" + tsFormattedFile
                logging.debug("Renaming %s to %s",nfcapdCurrent,nfcapdDummy)
                shutil.move(nfcapdCurrent, nfcapdDummy)
                
                # Copy *.dat file to 'parsed' folder
                netflow_dat_manual_file = netflow_dat_manual_folder + obsToProcess
                netflow_parsed_file = netflow_parsed_folder + "output-netflow_" + tsFormattedFile + ".dat"
                logging.debug("Copying netflow manually generated file %s to %s ",netflow_dat_manual_file, netflow_parsed_file)
                shutil.copyfile(netflow_dat_manual_file, netflow_parsed_file)                
            
                logging.debug("Waiting for %s s ...",schedulingTimer)
                sleep(schedulingTimer)
                obsCounter = obsCounter + 1
                
                
            except KeyboardInterrupt:
                logging.info("KeyboardInterrupt received. Exiting ...")
                end = True
            except Exception:
                logging.warning("Probably we have reached the end of the observations. ERROR: %s", sys.exc_info()[1])
                end = True