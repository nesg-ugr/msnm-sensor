# -*- coding: utf-8 -*-

"""
    :mod:`Sensor module`
    ===========================================================================
    :synopsis: Main methods for diagnostics and anomaly detection.
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg.ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

import sys
from msnm.modules.ma.model import Model
from msnm.utils import datautils as tools, datautils, dateutils
import numpy as np
import logging
from msnm.exceptions.msnm_exception import SensorError, MSPCError, MSNMError,\
    ModelError
from msnm.modules.config.configure import Configure

class Sensor():
    """

    *MSNM Sensor main module*. It contains the corresponding functionalities for diagnosis and anomaly detection.

    Attributes
    ----------
    _model: msnm.ma.Model
        Represents the multivariate model
    _mspc: msnm.ma.MSPC
        MSPC techniques
    _data: numpy.ndarray
        [NxM] calibration data array

    See Also
    --------
    msnm.ma.model
    msnm.ma.mspc
    msnm.utils
    """

    def __init__(self):
        self._model = Model()
        self._mspc = self._model.get_mspc()
        self._data = 0.0

    def do_calibration(self,**kwargs):
        """
        Starting point of the calibration procedure

        Raises
        ------
        SensorError, MSNMError

        """

        method_name = "do_calibration()"

        # Time stamp
        ts = dateutils.get_timestamp()

        # Get configuration
        config = Configure()
        # Get root path for creating data files
        rootDataPath = config.get_config()['GeneralParams']['rootPath']
        model_backup_path = config.get_config()['Sensor']['model']

        model_backup_file = rootDataPath + model_backup_path + "model_" + ts + ".json"

        try:
            # Model calibration init
            self._model.calibrate(self._data, **kwargs)

            # Get the JSON of the model
            json_model = datautils.model2json( self._model, ts)

            # Save the model
            datautils.save2json(json_model, model_backup_file)

        except ModelError as eme:
            raise SensorError(self,eme.msg,method_name)
        except MSNMError as emsnm:
            raise emsnm

    def do_dynamic_calibration(self,**kwargs):
        """
        Starting point for the dynamic calibration procedure

        Raises
        ------
        SensorError, MSNMError

        """

        method_name = "do_dynamic_calibration()"

        logging.info("Doing dynamic calibration ...")

        # Time stamp
        ts = dateutils.get_timestamp()

        # Get configuration
        config = Configure()
        model_backup_path = config.get_config()['Sensor']['model']
        model_backup_file = model_backup_path + "model_" + ts + ".json"

        try:
            # Model calibration init
            self._model.calibrate_dynamically(self._data, **kwargs)

            # Get the JSON of the model
            logging.debug("Saving the current model")
            json_model = datautils.model2json( self._model, ts)

            # Save the model
            datautils.save2json(json_model, model_backup_file)

        except ModelError as me:
            logging.error("Error doing dynamic calibration: %s",me.get_msg())
            raise SensorError(self,me.get_msg(),method_name)
        except MSNMError as emsnm:
            logging.error("Error doing dynamic calibration: %s",emsnm.get_msg())
            raise emsnm

        logging.info("End of doing dynamic calibration...")

    def do_monitoring(self,test):
        """
        Compute the Q and D statistics from a new observation ``test``

        Return
        ------
        Qst: float64
            Q statistic
        Dst: float64
            D statistic

        Raises
        ------
        SensorError, MSNMError

        """

        logging.info("Running do_monitoring ...")

        method_name = "do_monitoring()"

        # Check the data type as ndarray
        if not isinstance(test, np.ndarray):
            raise SensorError(self,"Data is not an ndarray",method_name)

        try:
            # Is the model calibrated?
            #TODO make a method that checks if the model is complete.
            if (self._model.get_data().shape[0] <= 1) or (self._model.get_data().shape[1] <= 1):
                raise SensorError(self,"Data does not has [NxM] dimensions",method_name)


            if test.shape[1] != self._model.get_data().shape[1]:
                logging.error("Test and calibration data does not match. Test %s != Cal %s ", test.shape,self._model.get_data().shape)
                raise SensorError(self,"Test and calibration data does not match.",method_name)

        except IndexError:
            raise SensorError(self,sys.exc_info()[0], method_name)

        try:

            logging.debug("Preprocessing the observation of %s.",test.shape)
            # data test autoscaled with the average and standard deviation from the original data
            testcs = tools.preprocess2Dapp(test,self._model.get_av(),self._model.get_sd())

            logging.debug("Computing statistics ...")
            # compute Q and D statistics
            self._mspc.computeQst(testcs, self._model.get_pca().getLoadings())
            logging.debug("Qst obtained: %s", self._mspc.getQst())
            self._mspc.computeDst(testcs, self._model.get_pca().getLoadings(), self._model.get_pca().getScores())
            logging.debug("Dst obtained: %s", self._mspc.getDst())

        except MSPCError:
            raise SensorError(self,sys.exc_info()[1], method_name)
        except MSNMError as e:
            raise e

        return self._mspc.getQst(), self._mspc.getDst()

    def do_diagnosis(self, test, dummy):
        """
        Diagnosis of an anomalous observation ``test``. Right now oMEDA is the
        selected method to do this.

        Raises
        ------
        SensorError, MSNMError

        """

        logging.info("Running do_monitoring ...")

        method_name = "do_diagnosis()"

        # Check the data type as ndarray
        if not isinstance(test, np.ndarray):
            raise SensorError(self,"Data is not a ndarray",method_name)

        # Check dummy ndarray
        if not isinstance(dummy, np.ndarray):
            raise SensorError(self,"Dummy vector is not a ndarray",method_name)

        try:
            # Is the model calibrated?
            #TODO make a method that checks if the model is complete.
            if (self._model.get_data().shape[0] <= 1) or (self._model.get_data().shape[1] <= 1):
                raise SensorError("Data does not has [NxM] dimensions",method_name)
        except IndexError:
            raise SensorError(self,sys.exc_info()[0],method_name)

        try:
            logging.debug("Preprocessing the observation of %s.",test.shape)
            # data test autoscaled with the average and standard deviation from the original data
            testcs = tools.preprocess2Dapp(test,self._model.get_av(),self._model.get_sd())

            logging.debug("Computing oMEDA ...")
            # Computes oMEDA
            self._mspc.computeoMEDA(testcs, dummy, self._model.get_pca().getLoadings())

        except MSPCError:
            raise SensorError(self,sys.exc_info()[1], method_name)
        except MSNMError as e:
            raise e

        return self._mspc.getoMEDAvector()


    # Getter & Setter methods
    def get_model(self):
        return self._model

    def get_mspc(self):
        return self._mspc


    def get_data(self):
        return self._data


    def set_model(self, value):
        self._model = value


    def set_data(self, value):
        self._data = value


    def del_model(self):
        del self._model


    def del_data(self):
        del self._data
