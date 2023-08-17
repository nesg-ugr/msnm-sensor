# -*- coding: utf-8 -*-
"""
    :mod:`msnmsensor`
    ===========================================================================
    :synopsis: Main class
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

from msnm.sensor import Sensor
from msnm.exceptions.msnm_exception import MSNMError, ConfigError
import sys, traceback
import os
import signal
import time
import numpy as np
import pandas as pd
import yaml
import logging.config
from msnm.modules.config.configure import Configure
from msnm.modules.com.networking import TCPServerThread, \
    MSNMTCPServerRequestHandler, MSNMTCPServer
from msnm.utils import datautils
from msnm.utils import dateutils
from msnm.modules.source.manager import SourceManager, SourceManagerMasterThread
import threading
from msnm.modules.source.remote import RemoteSource
import importlib
import argparse
from msnm.utils.offlineutils import OfflineThread
from msnm.modules.com.websocket import Websocket
from msnm.modules.com.api import app
import uvicorn


def main(config_file):
    # Get the configuration params and load it into a singleton pattern
    sensor_config_params = Configure()

    try:
        # Application config params
        sensor_config_params.load_config(config_file)

    except ConfigError as ece:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=10, file=sys.stdout)
        ece.print_error()
        exit(1)

    try:

        # Logging config
        logging.config.dictConfig(
            yaml.load(open(sensor_config_params.get_config()['GeneralParams']['logConfigFile'], 'r')))
    except ConfigError as ece:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=10, file=sys.stdout)
        ece.print_error()
        exit(1)

    # Run API server
    server_thread = threading.Thread(target=run_api_server)
    server_thread.start()

    # Create a Sensor
    sensor = Sensor()

    # Model variables and observation calibration.
    var_names = datautils.getAllVarNames()
    x = np.empty(0)

    if sensor_config_params.get_config()['Sensor']['staticCalibration']['randomCalibration']:
        # Random generated static calibration matix
        nobs = sensor_config_params.get_config()['Sensor']['staticCalibration']['randomCalibrationObs']
        x = datautils.generateRandomCalObsMatrix(nobs, len(var_names))
    else:
        # Get calibration matrix from a CSV file
        x = pd.read_csv(sensor_config_params.get_config()['Sensor']['staticCalibration']['calibrationFile'],
                        index_col=0).values

    # Get root path for creating data files
    rootDataPath = sensor_config_params.get_config()['GeneralParams']['rootPath']

    try:
        try:
            # Create monitoring dirs to save the results and the observations created
            if not os.path.exists(rootDataPath + sensor_config_params.get_config()['Sensor']['observation']):
                os.makedirs(rootDataPath + sensor_config_params.get_config()['Sensor']['observation'])
            if not os.path.exists(rootDataPath + sensor_config_params.get_config()['Sensor']['output']):
                os.makedirs(rootDataPath + sensor_config_params.get_config()['Sensor']['output'])
            if not os.path.exists(rootDataPath + sensor_config_params.get_config()['Sensor']['model']):
                os.makedirs(rootDataPath + sensor_config_params.get_config()['Sensor']['model'])
            if not os.path.exists(rootDataPath + sensor_config_params.get_config()['Sensor']['diagnosis']):
                os.makedirs(rootDataPath + sensor_config_params.get_config()['Sensor']['diagnosis'])
        except OSError as oe:
            logging.error("Sensor results directory cannot be created: %s", oe)
            exit(1)
        except Exception as e:
            traceback.print_exc()
            exit(1)

        # CALIBRATION PHASE
        # Get the number of latent variables configured
        lv = sensor_config_params.get_config()['Sensor']['lv']
        # Preprocessing method
        prep = sensor_config_params.get_config()['Sensor']['prep']
        # Phace to compute UCLD
        phase = sensor_config_params.get_config()['Sensor']['phase']

        sensor.set_data(x)
        sensor.do_calibration(phase=phase, lv=lv, prep=prep)
        logging.debug("UCLd = %s", sensor.get_model().get_mspc().getUCLD())
        logging.debug("UCLq = %s", sensor.get_model().get_mspc().getUCLQ())

        # Initial ts associated to the current monitoring interval
        ts = dateutils.get_timestamp()
        sensor_config_params.set_general_config_param('ts_monitoring_interval', ts)

        # Load local data sources
        local_dict = {}
        try:
            src_local = sensor_config_params.get_config()['DataSources']['local']

            logging.debug("Loading %s local sources %s.", len(src_local), list(src_local.keys()))

            for i in list(src_local.keys()):

                # Create the associated directories
                if not os.path.exists(rootDataPath + src_local[i]['raw']):
                    os.makedirs(rootDataPath + src_local[i]['raw'])
                if not os.path.exists(rootDataPath + src_local[i]['processed']):
                    os.makedirs(rootDataPath + src_local[i]['processed'])
                if not os.path.exists(rootDataPath + src_local[i]['parsed']):
                    os.makedirs(rootDataPath + src_local[i]['parsed'])

                # Create a dynamic instance
                # Example: MyClass = getattr(importlib.import_module(module_name), class_name)
                LocalSource = getattr(importlib.import_module(src_local[i]['moduleName']), i)
                local_dict[i] = LocalSource()
                local_dict[i].start()  # Run the thread associated

        except KeyError as ke:
            logging.warning("There are no local sources configured: %s", ke)
        except Exception as e:
            traceback.print_exc()
            exit(1)

        # Load remote data sources
        remote_dict = {}
        try:
            src_remote = sensor_config_params.get_config()['DataSources']['remote']

            logging.debug("Loading %s remote sources %s.", len(src_remote), list(src_remote.keys()))

            for i in list(src_remote.keys()):

                # Create the associated directories
                if not os.path.exists(rootDataPath + src_remote[i]['raw']):
                    os.makedirs(rootDataPath + src_remote[i]['raw'])
                if not os.path.exists(rootDataPath + src_remote[i]['parsed']):
                    os.makedirs(rootDataPath + src_remote[i]['parsed'])

                # Add the remote source
                remote_dict[i] = RemoteSource()

        except KeyError as ke:
            logging.warning("There are no remote sources configured: %s", ke)
        except OSError as oe:
            logging.error("Remote data source directory can not be created: %s", oe)
            exit(1)

        # Listening for incoming packets from remote sensors
        server_address = sensor_config_params.get_config()['Sensor']['server_address']
        server = MSNMTCPServer((server_address['ip'], server_address['port']), MSNMTCPServerRequestHandler)
        server.set_remotes(remote_dict)
        tcpServer = TCPServerThread(server)
        tcpServer.setName("TCPServer")
        tcpServer.start()

        # All data sources
        sources_dict = local_dict
        sources_dict.update(remote_dict)
        sources_dict = datautils.sort_dictionary(sources_dict, order='asc')

        # Create a Websocket
        ws_address = sensor_config_params.get_config()['Sensor']['ws_address']
        websocket = Websocket(ws_address['ip'], ws_address['port'])

        # Source management
        manager = SourceManager(sensor, websocket)
        manager.connect_websocket()
        manager.set_data_sources(sources_dict)
        managerThread = SourceManagerMasterThread(manager)
        managerThread.setName("SourceManagerMasterThread")
        managerThread.start()

        # Default static mode
        staticMode = False

        # Are there local sources?
        if 'local' in list(sensor_config_params.get_config()['DataSources'].keys()):
            # Check if the offline mode is enabled
            # TODO: enable this funcionality and extend this functionality to all available data sources
            # staticMode = sensor_config_params.get_config()['DataSources']['local']['Netflow']['staticMode']
            # If we are in static mode we launch the offilne thread

            offlineThread = OfflineThread()
            # TODO: enable this funcionality
            if staticMode:
                offlineThread.setName("OffLineThread")
                offlineThread.start()
                logging.debug("Offline thread has been launched ...")

        # To stop the main thread
        continueMainThread = True

        # Main loop
        while continueMainThread:
            print(sensor_config_params.get_config()['Sensor'])
            # static mode?
            if staticMode:
                if not offlineThread.isAlive():
                    offlineThread.stop()
                    continueMainThread = False

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received ...")
        exc_type, exc_value, exc_traceback = sys.exc_info()
    except ConfigError as ece:
        logging.error(ece.print_error())
    except MSNMError as se:
        logging.error(se.print_error())
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=5, file=sys.stdout)
    finally:
        logging.info("Stopping all services ...")

        # Stop all local data sources threads
        for i in list(local_dict.values()):
            i.stop()
        try:
            if isinstance(tcpServer, TCPServerThread): tcpServer.stop()
        except UnboundLocalError:
            logging.warning("TCPServerThread is not running, so it will not stopped.")
        try:
            if isinstance(managerThread, SourceManagerMasterThread): managerThread.stop()
        except UnboundLocalError:
            logging.warning("SourceMangerMasterThread is not running, so it will not stopped.")
        try:
            if isinstance(offlineThread, OfflineThread): offlineThread.stop()
        except UnboundLocalError:
            logging.warning("Offline thread is not running, so it will not stopped.")

        for i in threading.enumerate():
            if i is not threading.currentThread():
                logging.debug("Waiting for %s thread ...", i.name)
                i.join()
        logging.info("Exiting ...")
        exit(1)


def signalHandler(signum, frame):
    if signum == signal.SIGINT:
        raise KeyboardInterrupt("Signal Interrupt")
    else:
        logging.debug("Signal handler do not recognize signal number %s", signum)


def getArguments():
    """
    Function to get input arguments from configuration file
    :return: args
	"""

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='''Multivariate Statistical Network Monitoring - Sensor (MSNM Sensor)''')
    parser.add_argument('config', metavar='CONFIG', help='Sensor configuration File.')
    args = parser.parse_args()
    return args

def run_api_server():
    uvicorn.run(app, host="127.0.0.1", port=8989)


if __name__ == "__main__":
    # SIGINT registration to manage them outside
    signal.signal(signal.SIGINT, signalHandler)

    # Check the number of scripts params
    #nparams = len(sys.argv)

    #if nparams < 2:
    #    print("Use: msnmsensor.py <path_to_config_file> ")
    #    print("Example of use: msnmsensor.py ../config/sensor.yaml")
    #    exit(1)

    args = getArguments()

    main(args.config)
