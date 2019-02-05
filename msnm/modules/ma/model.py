# -*- coding: utf-8 -*-

"""
    :mod:`MSM (Multivariate System Model) Module`
    ===========================================================================
    :synopsis: Multivariate Model container
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

from msnm.modules.ma.pca import PCA
from msnm.utils import datautils as tools
from msnm.modules.ma.mspc import MSPC
from msnm.exceptions.msnm_exception import MSNMError, ModelError, PCAError,\
    MSPCError
import numpy as np
import logging

class Model:
    """
    *Multivariate Model*
        
    Attributes
    ----------
    _data : numpy.ndarray
        [NxM] Data calibration matrix
    _av : numpy.ndarray
        Variable average in ´´_data´´ calibration matrix [1xM] array
    _sd : numpy.ndarray
        Variable standard deviation in ´´_data´´ calibration matrix [1xM] array
    _prep : int
        Choose the preprocessing method:
           0: no preprocessing 
           1: mean-centering 
           2: auto-scaling (default)
    _pca : PCA instance
        PCA instance
    _lv : int
        Number of LVs (Latent Variables) used in calibration (by default is 3)
    _alpha : float
        Confident interval to compute the control limits
    _phase : int
        Choose the phase to compute UCLd:           
           1: Phase I 
           2: Phase II (default)
    _mspc: MSPC instance
        MSPC instance
    _UCLq: float
        UCL limit for Q-statistic
    _UCLd: float
        UCL limit for D-statistic        
        
    See Also
    --------
    msnm.modules.ma.pca
    msnm.modules.ma.mspc
    msnm.utils
    numpy
    sys
    
    """
   
    def __init__(self):
        self._data = np.zeros([])
        self._dataxcs = np.zeros([])
        self._dataXX = np.zeros([])
        self._batch = {}
        self._av = np.zeros([])
        self._sd = np.zeros([])
        self._N = 0
        self._lambda = 0
        self._prep = 2 # Auto-scaled   
        # TODO it could be a Model in general PCA(Model):    
        self._pca = PCA()
        self._lv = 3 # Latent variables, pcs in PCA
        self._alpha = 0.01 
        self._phase = 2 # UCLD phase II
        self._mspc = MSPC()
        
    def calibrate(self, data, **kwargs):
        """       
        Model calibration function
        
        Parameters
        ----------        
        data: numpy.ndarray
            [NxM] calibration matrix
        prep (optional): int
            Choose the preprocessing method:
               0: no preprocessing 
               1: mean-centering 
               2: auto-scaling (default)
        lv (optional): int
            Number of LVs (Latent Variables) used in calibration (by default is 3)        
        phase (optional): int
            Choose the phase to compute UCLd:           
               1: Phase I 
               2: Phase II (default)
               
        Raises
        ------
        ModelError
            When some parameter is not correctly passed o some ´´IndexError´´
            is raised by numpy 
                
            
        Example
        -------
        >>> from msnm.modules.ma.model import Model
        >>>
        >>> # Original data 
        >>> originalData = './datatest/real/data_test_model_cmp3_clean.mat'
        
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['Xclean']
        
        >>> model = Model()
        >>> model.calibrate(x,prep=2, lv=3, phase=2)
        
        >>> print "UCLq --> %f" % model.get_mspc().getUCLQ()
        >>> print "UCLd --> %f" % model.get_mspc().getUCLD()
                                            
        """
        
        method_name = "calibrate()"
        
        # Check the data type as ndarray
        if not isinstance(data, np.ndarray):
            raise ModelError(self,"Data is not an ndarray", method_name)
        # Data must be a [NxM] ndarray
        if (data.shape[0] <= 1) or (data.shape[1] <= 1):
            raise ModelError(self,"Data does not has [NxM] dimensions", method_name)
            
        try:
            
            # TODO: currently weights is not implemented in prepprocess2D        
            weights = np.ones((data.shape[0],1))
            
            # Check optional parameters
            if 'prep' in kwargs:
                self._prep = kwargs['prep']            
            if 'lv' in kwargs:
                self._lv = kwargs['lv']
            if 'phase' in kwargs:
                self._phase = kwargs['phase']
              
            # Set data
            self._data = data
        
            # Data preprocess
            self._dataxcs, self._av, self._sd = tools.preprocess2D(self._data,self._prep,weights)
             
            # Compute PCA
            self._pca.setData(self._dataxcs)
            self._pca.setPCs(self._lv)
            self._pca.runPCA()
                     
            # Compute UCLs
            self._mspc.computeUCLQ(self._pca.getResidual(), self._alpha)             
            logging.debug("UCLq obtained: %s",self._mspc.getUCLQ())
            self._mspc.computeUCLD(self._lv, data.shape[0], self._alpha, self._phase)
            logging.debug("UCLd obtained: %s",self._mspc.getUCLD())
        
        except PCAError as epca:
            raise ModelError(self,epca.msg,method_name)
        except MSPCError as emspc:
            raise ModelError(self,emspc.msg,method_name)
        except MSNMError as emsnm:
            raise emsnm
        
    def calibrate_dynamically(self, data, **kwargs):
        """       
        Model calibration function
        
        Parameters
        ----------        
        data: numpy.ndarray
            [NxM] calibration matrix
        prep (optional): int
            Choose the preprocessing method:
               0: no preprocessing 
               1: mean-centering 
               2: auto-scaling (default)
        lv (optional): int
            Number of LVs (Latent Variables) used in calibration (by default is 3)        
        phase (optional): int
            Choose the phase to compute UCLd:           
               1: Phase I 
               2: Phase II (default)
               
        Raises
        ------
        ModelError
            When some parameter is not correctly passed o some ´´IndexError´´
            is raised by numpy 
                
            
        Example
        -------
        >>> from msnm.modules.ma.model import Model
        >>>
        >>> # Original data 
        >>> originalData = './datatest/real/data_test_model_cmp3_clean.mat'
        
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['Xclean']
        
        >>> model = Model()
        >>> model.calibrate(x,prep=2, lv=3, phase=2)
        
        >>> print "UCLq --> %f" % model.get_mspc().getUCLQ()
        >>> print "UCLd --> %f" % model.get_mspc().getUCLD()
                                            
        """
        
        method_name = "calibrate()"
        
        # Check the data type as ndarray
        if not isinstance(data, np.ndarray):
            raise ModelError(self,"Data is not an ndarray", method_name)
        # Data must be a [NxM] ndarray
        if (data.shape[0] < 1) or (data.shape[1] < 1):
            raise ModelError(self,"Data does not has [NxM] dimensions", method_name)
            
        try:
            
            # TODO: currently weights is not implemented in prepprocess2D        
            weights = np.ones((data.shape[0],1))
            
            # Check optional parameters
            if 'prep' in kwargs:
                self._prep = kwargs['prep']            
            if 'lv' in kwargs:
                self._lv = kwargs['lv']
            if 'phase' in kwargs:
                self._phase = kwargs['phase']
            if 'lamda' in kwargs:
                self._lambda = kwargs['lamda']
              
            # Set data
            self._data = data
            
            # Removing NaN if they exist
            # TODO test this method
            #data = tools.averagedMissingData(data, self._av)
            
            # Data preprocessing
            self._dataxcs, self._av, self._sd, self._N = tools.preprocess2Di(data, self._prep, self._lambda, self._av, self._sd, self._N, weights)
            
            # EWMA cross-product
            self._dataXX = self._lambda * self._dataXX + np.dot(self._dataxcs.T, self._dataxcs)
             
            # Compute PCA
            self._pca.setData(self._dataxcs)
            self._pca.setPCs(self._lv)
            self._pca.runPCA(method='eig', xxcrossdata=self._dataXX)
                     
            # Compute UCLs
            self._mspc.computeUCLQ(self._pca.getResidual(), self._alpha)
            logging.debug("UCLq obtained: %s",self._mspc.getUCLQ())            
            self._mspc.computeUCLD(self._lv, data.shape[0], self._alpha, self._phase)
            logging.debug("UCLd obtained: %s",self._mspc.getUCLD())
        
        except PCAError as epca:
            raise ModelError(self,epca.msg,method_name)
        except MSPCError as emspc:
            raise ModelError(self,emspc.msg,method_name)
        except MSNMError as emsnm:
            raise emsnm

    
    # Getter, setter and del methods
    def get_data(self):
        return self._data


    def get_av(self):
        return self._av


    def get_sd(self):
        return self._sd


    def get_pca(self):
        return self._pca


    def get_lv(self):
        return self._lv


    def get_alpha(self):
        return self._alpha


    def get_phase(self):
        return self._phase


    def get_mspc(self):
        return self._mspc

    def set_data(self, value):
        self._data = value


    def set_av(self, value):
        self._av = value


    def set_sd(self, value):
        self._sd = value


    def set_pca(self, value):
        self._pca = value


    def set_lv(self, value):
        self._lv = value


    def set_alpha(self, value):
        self._alpha = value


    def set_phase(self, value):
        self._phase = value


    def set_mspc(self, value):
        self._mspc = value

    def del_data(self):
        del self._data


    def del_av(self):
        del self._av


    def del_sd(self):
        del self._sd


    def del_pca(self):
        del self._pca


    def del_lv(self):
        del self._lv


    def del_alpha(self):
        del self._alpha


    def del_phase(self):
        del self._phase


    def del_mspc(self):
        del self.__mspc


        
    
            
        
        
        