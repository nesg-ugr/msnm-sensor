# -*- coding: utf-8 -*-
"""
    :mod:`manager`
    ===========================================================================
    :synopsis: It is in charge of to manage the monitoring process of all data sources.
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

from msnm.modules.source.source import Source
from msnm.modules.thread.thread import MSNMThread
from time import sleep
from datetime import datetime
from datetime import timedelta
from msnm.modules.config.configure import Configure
import logging
from msnm.exceptions.msnm_exception import DataSourceError, SensorError,\
    MSNMError
import sys
import importlib
from msnm.utils import dateutils, datautils
import traceback
import numpy as np
from msnm.modules.com.packet import DataPacket, Packet
from msnm.modules.com.networking import TCPClient, TCPClientThread

class SourceManager(Source):

    def __init__(self, sensor):
        self._sensor = sensor
        self._sources = {} # Contains all data sources ('Source name', source_instance)
        self._batch = {}
        self._packet_sent = 0
        self._current_batch_obs = 0

    def set_data_sources(self,sources):
        self._sources = sources

    def get_number_source_variables(self, source, source_name):
        # TODO: get this parameter from the flow parser sources configuration
        config = Configure()

        vars_number = 0
        if source._type == Source.TYPE_L:
            vars_number = len(config.get_config()['DataSources'][source._type][source_name]['parserContents'][Source.S_VARIABLES])
        else:
            vars_number = config.get_config()['DataSources'][source._type][source_name]['parserVariables']

        return vars_number

    def launch_monitoring(self,ts):
        """
        Once the parsing (flow parser) procedure is done, this method is in charge of to start the monitoring
        process

        Raises
        ------
        MSNMError

        """

        method_name = "launch_monitoring()"

        # Configuration
        config = Configure()
        # Get root path for creating data files
        rootDataPath = config.get_config()['GeneralParams']['rootPath']

        obs_generated_path = rootDataPath + config.get_config()['Sensor']['observation'] # path to save the complete observation joining all data sources
        batch_obs = config.get_config()['Sensor']['dynamiCalibration']['B'] # number of observation in a batch for EWMA calibration
        lambda_param = config.get_config()['Sensor']['dynamiCalibration']['lambda'] # fogetting parameter for EWMA calibration
        dyn_cal_enabled = config.get_config()['Sensor']['dynamiCalibration']['enabled'] # is the dynamic calibration activated?
        output_generated_path = rootDataPath + config.get_config()['Sensor']['output'] # path to save the Q and T statistics obtained from the previous observation
        missingDataMethods = config.get_config()['Sensor']['missingData']['missingDataMethods'] # Missing data available methods
        missingDataSelectedMethod = config.get_config()['Sensor']['missingData']['selected'] # Get the selected missing data method
        missingDataModule = config.get_config()['Sensor']['missingData']['missingDataModule'] # Missing data available methods
        valuesFormat = config.get_config()['GeneralParams']['valuesFormat'] # how the variables of the complete observation are saved

        logging.debug("Launch monitoring for %s ",ts)

        try:
            logging.debug("Building the observation at %s for %s sources.",ts,self._sources.keys())
            # Build the observation for monitoring
            test = []
            for i in self._sources.keys():
                # Get the number of variables of source i
                i_variables = self.get_number_source_variables(self._sources[i],i)
                logging.debug("Source %s has %s variables.",i,i_variables)
                # Get the source output parsed file for the current
                i_parsed_file = self._sources[i]._files_generated[ts]
                logging.debug("File generated of source %s at %s: %s",i,ts,i_parsed_file)

                if i_parsed_file:
                    # Load the file
                    if self._sources[i]._type == Source.TYPE_L:

                        # static mode?
                        # TODO: next version
                        #staticMode = config.get_config()['DataSources'][self._sources[i]._type][i]['staticMode'];
                        staticMode = False

                        if not staticMode: # online or dynamic mode
                            i_test = np.loadtxt(i_parsed_file, comments="#", delimiter=",")
                        else: # offline or static mode
                            # TODO it is just a patch to remove in_npackets_verylow e in_nbytes_verylow like in matlab experiment and just for Netflow!!!
                            # look for a more smart way to do this e.g., by configuration params
                            i_test = np.loadtxt(i_parsed_file, comments="#", delimiter=",",usecols=range(1,i_variables + 1 + 2))

                            logging.debug("Offline mode for source %s. Observation size of %s",i,i_test.shape)

                            mask = np.ones(i_test.shape,dtype=bool)
                            # in_npackets_verylow index in matlab is 119 --> 119 in numpy
                            # in_nbytes_verylow index in matlab is 129 --> 129 in numpy
                            mask[118] = False
                            mask[128] = False
                            i_test = i_test[mask]

                            logging.debug("Offline mode for source %s. Observation size of %s after removing unuseless variables.",i,i_test.shape)

                    elif self._sources[i]._type == Source.TYPE_R:
                        i_test = np.loadtxt(i_parsed_file, comments="#", delimiter=",")
                    else:
                        logging.warn("Source %s does not has a valid type. Type: %s",i,self._sources[i]._type)
                else:
                    # Missing values are replaced with NaN values
                    i_test = np.empty(i_variables)
                    i_test[:] = np.nan

                # Test observation
                test = np.concatenate((test,i_test),axis=0)

            # 1xM array
            test = test.reshape((1,test.size))

            # Dynamic invocation of the selected data imputation method if needed
            if np.isnan(test).any():
                missingDataMethod = getattr(importlib.import_module(missingDataModule), missingDataMethods[missingDataSelectedMethod])
                logging.debug("Invoking %s method for data imputation for observation at %s",missingDataMethod.func_name,ts)
                # Calling the corresponding method
                test = missingDataMethod(obs=test,model=self._sensor._model)

            obs_generate_file = obs_generated_path + "obs_" + ts + ".dat"
            np.savetxt(obs_generate_file, test, fmt=valuesFormat,delimiter=",", header=str(datautils.getAllVarNames()),comments="#")

            logging.debug("Observation generated of %s variables at %s.",test.size,ts)

            # if the dynamic calibration enabled?
            if dyn_cal_enabled:

                # Increments the number of observation
                self._current_batch_obs = self._current_batch_obs + 1

                logging.debug("obs %s added to the batch as number %s.",ts,self._current_batch_obs)

                # Add the observation
                self._batch[ts] = {}
                self._batch[ts]['file'] = obs_generate_file
                self._batch[ts]['data'] = test

                # Once we reached the number of batch observations, we can do the dynamic calibration
                if self._current_batch_obs == batch_obs:
                    # data for calibration
                    x = np.array([])
                    x = x.reshape((0,test.size))

                    # Build the [NxM] data for the calibration
                    #print(self._batch.keys())
                    for i in self._batch.keys():
                        logging.debug("batch at %s -> %s", i, self._batch[i]['data'].shape)
                        x = np.vstack((x,self._batch[i]['data']))

                    #print(x)
                    #print(type(x))

                    # Build the model
                    self._sensor.set_data(x)
                    self._sensor.do_dynamic_calibration(phase=2,lv=3,lamda=lambda_param)

                    # Reset the counter
                    self._current_batch_obs = 0

                    # Removing all batch observations
                    self._batch.clear()

            # Do monitoring
            Qst, Dst = self._sensor.do_monitoring(test)

        except SensorError as ese:
            raise MSNMError(self, ese.get_msg() ,method_name)
        except MSNMError as emsnme:
            raise emsnme

        logging.debug("MONITORING --> UCLd: %s | Dst: %s",self._sensor.get_model().get_mspc().getUCLD(),self._sensor.get_mspc().getDst())
        logging.debug("MONITORING --> UCLq: %s | Qst: %s",self._sensor.get_model().get_mspc().getUCLQ(),self._sensor.get_mspc().getQst())

        # Save the generated statistics
        output_generated_file = output_generated_path + "output_" + ts + ".dat"
        header = "UCLq:" + str(self._sensor.get_model().get_mspc().getUCLQ()) + ", UCLd:" + str(self._sensor.get_model().get_mspc().getUCLD())
        list_array = [self._sensor.get_mspc().getQst(),self._sensor.get_mspc().getDst()]
        statistics = np.array(list_array)
        statistics = statistics.reshape((1,statistics.size))
        np.savetxt(output_generated_file, statistics, fmt=valuesFormat, delimiter=",", header=header, comments="#")

        # Gets the remote sensor addressed to send the packet
        remote_addresses = config.get_config()['Sensor']['remote_addresses']

        # Send packets is there are someone for sending it!
        if remote_addresses:

            # Send the data packet to the corresponding sensor.
            dataPacket = DataPacket()
            # Packet sent counter increments
            self._packet_sent = self._packet_sent + 1
            dataPacket.fill_header({'id':self._packet_sent, 'sid':config.get_config()['Sensor']['sid'], 'ts':dateutils.get_timestamp(), 'type':Packet.TYPE_D})
            dataPacket.fill_body({'Q':self._sensor.get_mspc().getQst(), 'D':self._sensor.get_mspc().getDst()})

            logging.debug("Remote sources to send the packet #%s: %s",self._packet_sent,remote_addresses)

            for i in remote_addresses.keys():
                ip = remote_addresses[i]['ip']
                port = remote_addresses[i]['port']
                tcpClient = TCPClient()
                tcpClient.set_server_address((ip,port))
                tcpClient.set_packet_to_send(dataPacket)
                TCPClientThread(tcpClient).start()

        return test, Qst, Dst

class SourceManagerMasterThread(MSNMThread):
    def __init__(self, sourceManager_instance):
        super(SourceManagerMasterThread,self).__init__()
        self._sourceManager_instance = sourceManager_instance

    def run(self):

        logging.info("Running Source Master Manager ...")

        method_name = "run()"

        # Get configuration
        config = Configure()
        timer = config.get_config()['GeneralParams']['dataSourcesScheduling']
        timeout = config.get_config()['GeneralParams']['dataSourcesNotReadyWaitingTime']

        try:
            # Monitoring interval counter
            c_interval = 1

            # Doing until stop request
            while not self._stopped_event.isSet():

                # init of the monitoring interval
                t_init_interval = datetime.now()

                # end of the monitoring interval
                t_end_interval = t_init_interval + timedelta(seconds=timer)

                # max time for waiting a source
                t_max_interval = t_end_interval + timedelta(seconds=timeout)

                # ts associated to the current monitoring interval
                ts = dateutils.get_timestamp()

                # Start a thread to manage the sources ready for the current monitoring interval
                intervalSourceMonitoringThread = IntervalMonitoringSourceManagerThread(self._sourceManager_instance,t_init_interval,t_end_interval,t_max_interval, ts)
                intervalSourceMonitoringThread.setName("IntervalThread_" + str(c_interval))
                intervalSourceMonitoringThread.start()

                # Wait for the end of the interval
                logging.debug("Waiting for the next interval ...")
                sleep(timer)

                # Monitoring interval counter
                c_interval = c_interval + 1

        except Exception as detail:
            logging.error("Error in processing the data sources. Type: %s, msg: %s",sys.exc_info()[0],detail)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback ,limit=5, file=sys.stdout)
            raise DataSourceError(self, detail, method_name)

class IntervalMonitoringSourceManagerThread(MSNMThread):

    def __init__(self, sourceManager_instance, t_init_interval, t_end_interval, t_max_interval, ts):
        super(IntervalMonitoringSourceManagerThread,self).__init__()
        self._sourceManager_instance = sourceManager_instance
        self._sources_ready = {} # Contains which source is ready to process in this interval
        self._t_init = t_init_interval
        self._t_end = t_end_interval
        self._t_max = t_max_interval
        self._ts = ts

    def are_ready(self, ts):

        for i in self._sourceManager_instance._sources.keys():
            if self.is_ready(i, ts):
                self._sources_ready[i] = True
            else:
                self._sources_ready[i] = False

        # Are all the datasources ready? -> Check generated file
        return all(self._sources_ready.itervalues())

    def is_ready(self, source, ts):

        if ts in self._sourceManager_instance._sources[source]._files_generated.keys():
            return True
        else:
            return False

    def get_not_ready(self):

        not_ready_sources = {}

        for i in self._sourceManager_instance._sources.keys():
            if not self._sources_ready[i]:
                not_ready_sources[i] =  self._sourceManager_instance._sources[i]

        return not_ready_sources

    def run(self):

        logging.info("Monitoring sources from %s to %s with maximum time until %s",self._t_init,self._t_end,self._t_max)

        method_name = "run()"

        # Get configuration
        config = Configure()
        # root path for the data
        rootDataPath = config.get_config()['GeneralParams']['rootPath']

        timer = config.get_config()['GeneralParams']['dataSourcesPolling']
        diagnosis_backup_path = rootDataPath + config.get_config()['Sensor']['diagnosis'] # path to save diagnosis vector output
        valuesFormat = config.get_config()['GeneralParams']['valuesFormat'] # how the variables of the complete observation are saved


        try:

                # Set all data sources as non-ready
                for i in self._sourceManager_instance._sources.keys():
                    self._sources_ready[i] = False

                logging.debug("Checking sources at %s time interval.", self._ts)

                # End thread
                finish = False

                while not finish:

                    logging.debug("Data sources not ready at interval %s: %s",self._ts,self.get_not_ready().keys())

                    # Current time
                    tc = datetime.now()

                    # for each source
                    for i in self._sourceManager_instance._sources.keys():

                        # If the max time to wait is not reached and not all sources are ready
                        if tc <= self._t_max and not self.are_ready(self._ts):
                            # Source i is ready?
                            if self.is_ready(i, self._ts):
                                # Source 'i' is ready
                                self._sources_ready[i] = True

                        else:
                            # Get not ready sources for that ts
                            src_not_ready = self.get_not_ready()

                            # Create an empty dummy *.dat file for the missing sources
                            logging.debug("Data sources not ready: %s",src_not_ready.keys())

                            for i in src_not_ready.keys():
                                if src_not_ready[i]._type == Source.TYPE_R:
                                    parsed_file_path = rootDataPath + config.get_config()['DataSources'][Source.TYPE_R][i]['parsed']
                                else:
                                    parsed_file_path = rootDataPath + config.get_config()['DataSources'][Source.TYPE_L][i]['parsed']

                                dummy_file = parsed_file_path + "dummy_" + self._ts + ".dat"

                                # Creates a dummy empty file
                                with open(dummy_file,'w') as fw:
                                    fw.write("Empty dummy file indicating that there was no data available for that source at " + self._ts)

                                # For this ts the source is not ready
                                self._sourceManager_instance._sources[i]._files_generated[self._ts] = None

                                #logging.debug("Dummy file created : %s", dummy_file)
                                logging.debug("Files generated for source %s at %s: %s",i,self._ts,self._sourceManager_instance._sources[i]._files_generated)

                            # if the sensor has no remote sensor to send the statistics means that it is the root in the sensor hierarchy,
                            # so launch_monitoring is not necessary
                            remote_addresses = config.get_config()['Sensor']['remote_addresses']

                            # Do monitoring
                            test, Qst, Dst = self._sourceManager_instance.launch_monitoring(self._ts)

                            # Set up which observations are compared
                            dummy = np.zeros((1,test.shape[0]))
                            # We evaluate the observation 1
                            dummy[0,0] = 1

                            # Do diagnosis
                            diagnosis_vec = self._sourceManager_instance._sensor.do_diagnosis(test, dummy)

                            # Save the diagnosis
                            diagnosis_backup_file = diagnosis_backup_path + "diagnosis_" + self._ts + ".dat"
                            #datautils.save2json(diagnosis_vec.tolist(), diagnosis_backup_file)
                            np.savetxt(diagnosis_backup_file, diagnosis_vec, fmt=valuesFormat,delimiter=",", header=str(datautils.getAllVarNames()),comments="#")


                            if not remote_addresses:
                                logging.warning("There are no remote addresses configured. This sensor should be the root in the sensor hierarchy.")

                            # Finish the thread after launch the monitoring procedure
                            finish = True;

                            # Exit to start the new monitoring interval
                            break

                    # wait for polling time: waiting time for checking if the sources are ready
                    sleep(timer) # TODO: to customize on demand


        except Exception as detail:
            logging.error("Error in processing the data sources. Type: %s, msg: %s",sys.exc_info()[0],detail)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback ,limit=5, file=sys.stdout)
            raise DataSourceError(self, detail, method_name)
