# -*- coding: utf-8 -*-
"""
    :mod:`netflow`
    ===========================================================================
    :synopsis: It is in charge of to get, parser and process netflow based data sources
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

from msnm.modules.source.source import Source
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from msnm.modules.config.configure import Configure
from msnm.exceptions.msnm_exception import DataSourceError
from subprocess import call
import sys
import logging
import pandas as pd
import shutil
import os

class Netflow(Source):
    '''
    classdocs
    '''
    def __init__(self):
        super(Netflow,self).__init__()

        # Listen for new nfcapd files
        event_handler = NetFlowFileEventHandler(self)
        try:
            # Watch the new netflow generated files
            self._observer = Observer()
            self._observer.schedule(event_handler, self.config.get_config()['DataSources'][self._type][self.__class__.__name__]['captures'], recursive=False)
            self._observer.setName("Netflow")
            self._observer.start()
        except Exception as e:
            logging.error("Please check if %s folder for netflow captures is already created.",
                          self.config.get_config()['DataSources'][self._type][self.__class__.__name__]['captures'])
            raise e


    def start(self):

        nfcapdAutomatize = self.config.get_config()['DataSources'][self._type][self.__class__.__name__]['nfcapdAutomatize']
        if nfcapdAutomatize:
            self.run_nfcapd()
        else:
            logging.warn("nfcapd must have been initiated before!")

    def stop(self):

        nfcapdAutomatize = self.config.get_config()['DataSources'][self._type][self.__class__.__name__]['nfcapdAutomatize']
        if nfcapdAutomatize:
            #If nfcapd is already started we kill it!
            retcode = os.system("killall -9 nfcapd")
            if retcode == 0:
                logging.debug("nfcapd was succesfully killed ..")

        self._observer.stop()

    def run_nfcapd(self):
        """
        Runs the nfcapd daemon. This is in charge of to capture the traffic flow and generates the
        correspondiente nfcapd* files every certain scheduling time. This time is set up on demand.

        Raises
        ------
        DataSourceError

        """

        method_name = "run_nfcapd()"

        nfcapd_captures_folder = self.config.get_config()['DataSources'][self._type][self.__class__.__name__]['captures'] # Folder where the nfcapd will be generated
        timer = self.config.get_config()['GeneralParams']['dataSourcesScheduling'] # data source captures scheduling

        # TODO: compatibility for windows machines
        # If nfcapd is already started we kill it!
        retcode = os.system("killall -9 nfcapd")
        if retcode == 0:
            logging.debug("nfcapd was succesfully killed ..")

        logging.debug("Running nfcapd application. Captures will be generated in %s every %s seconds.",nfcapd_captures_folder,timer)

        # Call to nfcapd process.
        retcode = call("nfcapd -w -D -l " + str(nfcapd_captures_folder) + " -p 2055 -T +8 -t " + str(timer),shell=True)

        if retcode != 0:
            raise DataSourceError(self,"Error calling nfcapd ...", method_name)

    def run_nfdump(self,nfcapd_file_path, output_file_path):
        """
        From a new netflow file, it is in charge of to call nfdump to transform the byte based
        netflow files to a *.csv file as input of the flow parser.

        Raises
        ------
        MSNMError

        """

        method_name = "run_nfdump()"

        logging.info("Running nfdump ...")

        # Call to nfdump process.
        retcode = call("nfdump -r " + str(nfcapd_file_path) + " -q -o csv >> " + output_file_path,shell=True)

        if retcode != 0:
            raise DataSourceError(self,"Error calling nfdump", method_name)

        logging.debug("New nfdump csv generated: %s",output_file_path)

        try:
            # add new id column to merge in parser
            # TODO: build a more elaborated method to do this e.g., from a dateframe utils package
            df = pd.read_csv(output_file_path,header=None, index_col=0)
            df.loc[:,df.shape[1]] = range(100000, 100000 + df.shape[0])
            df.to_csv(output_file_path, encoding='utf-8', header=False)

        except ValueError:
            # FIXME: Sometimes nfcapd generates an empty file :( I do not why :(
            logging.warn("Nfdump file is empty, skipping ... ERROR: %s ",sys.exc_info()[0])
            raise DataSourceError(self,"Nfdump file is empty ....", method_name)

        except Exception:
            raise DataSourceError(self,sys.exc_info()[0], method_name)


class NetFlowFileEventHandler(FileSystemEventHandler):

    def __init__(self, netflow_instance):
        self._netflow_instance = netflow_instance

    def on_moved(self, event):
        """
            Called when a new file is renamed in the nfcapd output folder.
            This method is in charge of launch all sensor tasks which are mentioned
            in this class description
        """
        super(NetFlowFileEventHandler, self).on_moved(event)

        logging.info("Running netflow procedure ...")

        method_name = "on_moved()"

        # Get configuration
        config = Configure()
        # Get root path for creating data files
        rootDataPath = config.get_config()['GeneralParams']['rootPath']

        netflow_log_raw_folder = rootDataPath + config.get_config()['DataSources'][self._netflow_instance._type][self._netflow_instance.__class__.__name__]['raw']
        netflow_log_processed_folder = rootDataPath + config.get_config()['DataSources'][self._netflow_instance._type][self._netflow_instance.__class__.__name__]['processed']
        netflow_log_parsed_folder = rootDataPath + config.get_config()['DataSources'][self._netflow_instance._type][self._netflow_instance.__class__.__name__]['parsed']
        netflow_flow_parser_config_file = config.get_config()['DataSources'][self._netflow_instance._type][self._netflow_instance.__class__.__name__]['parserConfig']; # Parser configuration file for netflow

        #TODO: to be enabled
        #staticMode = config.get_config()['DataSources'][self._netflow_instance._type][self._netflow_instance.__class__.__name__]['staticMode'];
        staticMode = False

        try:
            # Time stamp
            #ts = dateutils.get_timestamp()

            # Get the ts provided by the recently generated nfcapd file
            list_splitted = event.dest_path.split('/')
            nfcapd_file_name = list_splitted[len(list_splitted) - 1]
            ts = nfcapd_file_name.split('.')[1]

            if not staticMode: # dynamic mode

                # Get *.csv from nfcapd file
                netflow_log_processed_file = netflow_log_processed_folder + "netflow_" + ts + ".csv"
                self._netflow_instance.run_nfdump(event.dest_path, netflow_log_processed_file)

                # Copy nfcapd file recently generated in raw folder
                netflow_log_raw_file = netflow_log_raw_folder + "nfcapd_" + ts
                logging.debug("Copying netflow raw file %s to %s ",event.dest_path, netflow_log_raw_file)
                shutil.copyfile(event.dest_path, netflow_log_raw_file)

                # Copy CSV file to parsed folder to be parsed by the flow parsed
                netflow_log_parsed_file = netflow_log_parsed_folder + "netflow_" + ts + ".csv"
                logging.debug("Copying netflow processed file %s to %s ",netflow_log_processed_file, netflow_log_parsed_file)
                shutil.copyfile(netflow_log_processed_file, netflow_log_parsed_file)

                # Flow parser
                logging.debug("Running flow parser for %s file config.",netflow_flow_parser_config_file)
                self._netflow_instance.launch_flow_parser(netflow_flow_parser_config_file)

                # Add the *.dat output from parser to the dict of generated files
                self._netflow_instance._files_generated[ts] = netflow_log_parsed_folder + "output-netflow_" + ts + ".dat"

                # Remove CSV file once it is parsed succesfully
                logging.debug("Deleting file %s",netflow_log_parsed_file)
                os.remove(netflow_log_parsed_file)

            else: # static mode

                # Add the *.dat output from parser to the dict of generated files
                # output-netflow_201701231335.dat file have previously copied from static_simulation.py script
                # In static mode the emulated nfcapd files has the name like  nfcapd.201701302000_2016001182312, where last ts after '_' is the ts of the statid *.dat
                # file
                tsFile = ts.split('_')[1]
                ts = ts.split('_')[0]

                self._netflow_instance._files_generated[ts] = netflow_log_parsed_folder + "output-netflow_" + tsFile + ".dat"


        #TODO when an exception is raised is not correctly caugh outside :(
        except DataSourceError as edse:
            logging.error("DataSourceError processing netflow source: %s",edse.get_msg())
            #raise edse
            # remove wrong file generated
#             logging.debug("Deleting file %s",netflow_log_parsed_file)
#             os.remove(netflow_log_parsed_file)
#             logging.debug("Deleting file %s",netflow_log_raw_file)
#             os.remove(netflow_log_raw_file)
#             logging.debug("Deleting file %s",netflow_log_processed_file)
#             os.remove(netflow_log_processed_file)
        except IOError:
            logging.error("Error managing files in netflow source: %s",sys.exc_info()[0])
            #raise DataSourceError(self, sys.exc_info()[0], method_name)
#             logging.debug("Deleting file %s",netflow_log_parsed_file)
#             os.remove(netflow_log_parsed_file)
#             logging.debug("Deleting file %s",netflow_log_raw_file)
#             os.remove(netflow_log_raw_file)
#             logging.debug("Deleting file %s",netflow_log_processed_file)
#             os.remove(netflow_log_processed_file)
