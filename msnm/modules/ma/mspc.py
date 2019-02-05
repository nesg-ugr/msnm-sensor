# -*- coding: utf-8 -*-

"""
    :mod:`MSPC module`
    ===========================================================================
    :synopsis: Set of MSPC techniques
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

import numpy as np
from scipy.stats import f as fisher
from scipy.stats import beta
from scipy.stats import norm
from numpy.linalg.linalg import LinAlgError
from msnm.exceptions.msnm_exception import MSPCError
import sys
import logging

class MSPC:
    """
    *MSPC utilities*
        
    Attributes
    ----------
    _Dst : numpy.ndarray
        D-statistic or Hotelling T2: [Nx1] array, one per each observation monitored
    _Qst : numpy.ndarray
        Q-statistic: [Nx1] array, one per each observation monitored
    _UCLQ : float64
        UCL for Q-statistic
    _UCLD : float64
        UCL for D-statistic
    _oMEDA : numpy.ndarray
        oMEDA array: [Mx1] one per each monitored variables
        
    See Also
    --------
    msnm.modules.ma.pca
    msnm.utils
    scipy.stats.f
    scipy.stats.beta
    scipy.stats.norm
    numpy
    """
   
    def __init__(self):
        self._Dst = 0.0
        self._Qst = 0.0
        self._UCLQ = 0.0
        self._UCLD = 0.0
        self._oMEDA = 0.0
        
    def computeQst(self,testcs,P):         
        """       
        Computes Q-statistic and set ``self._Qst`` class attribute
        
        Parameters
        ----------        
        testcs: numpy.ndarray
            [NxM] preprocessed billinear data set with the observations to be monitored.
        P: numpy.ndarray 
            [MxA] Matrix to perform the projection from the original to the latent subspace. 
            For PCA (testcs = T*P'), this is the matrix of loadings 
            
        Raises
        ------
        MSPCError
            When something is going wrong during the mathematical operations
            
        Example
        -------
        >>> from msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        >>> from msnm.modules.ma import mspc
        
        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov_mspc.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        >>> weights = np.ones((x.shape[0],1))
          
        >>> # data preprocess auto-scaled
        >>> xcs, average, scale = tools.preprocess2D(x,2,weights)
          
        >>> #PCA
        >>> pcaModel = pca.PCA()
        >>> pcaModel.setPCs(1) # like in mspc.m example
        >>> pcaModel.setData(xcs)
        >>> pcaModel.runPCA()
          
        >>> T = pcaModel.getScores()
        >>> P = pcaModel.getLoadings()
          
        >>> # anomalous data test
        >>> test = data['test']
          
        >>> # data test autoscaled
        >>> testcs = tools.preprocess2Dapp(test,average,scale)
        
        >>> # Computes the Q-statistics
        >>> mspcInstance = mspc.MSPC()
        >>> mspcInstance.computeDst(testcs,P,T)
        >>> mspcInstance.computeQst(testcs,P)
        
        >>> Get the result
        >>> Qst = mspcInstance.getQst()
        >>> print Qst
                                    
        """
        
        method_name = "computeQst()"
        
        try:
            #new scores from testcs and the loadings (Q) of the calibration model
            t = np.dot(testcs,P)
            
            # Model residuals from the observations in testcs
            e = testcs - np.dot(t,np.transpose(P))     
            
            # Computes Q-statistics from the observations in testcs
            self._Qst = np.sum(np.power(e,2),axis=1).reshape(testcs.shape[0],1);
            
            # Check is the statistic is and ndarray of [1x1] dimensions and get the float value
            if isinstance(self._Qst, np.ndarray):
                self._Qst = self._Qst[0,0]
            
            # TODO: Sometimes after computations numpy takes UCLq as complex with 0j imaginary part
            if isinstance(self._Qst, complex):
                logging.warn("Qst has a complex value of %s. Getting just the real part.",self._Qst)
                self._Qst = self._Qst.real
                
        except Exception:
            raise MSPCError(self,sys.exc_info()[0], method_name) 
        
        
    def computeDst(self, testcs, P, T):        
        """       
        Computes D-statistic and set ``self._Dst`` class attribute
        
        Parameters
        ----------        
        testcs: numpy.ndarray
            [NxM] preprocessed billinear data set with the observations to be monitored.
        P: numpy.ndarray 
            [MxA] Matrix to perform the projection from the original to the latent subspace. 
            For PCA (testcs = T*P'), this is the matrix of loadings
        T: numpy.ndarray 
            [MxA] Matrix to perform the projection from the original to the latent subspace. 
            For PCA (testcs = T*P'), this is the matrix of scores
            
        Raises
        ------
        MSPCError
            When something is going wrong during the mathematical operations 
            
        Example
        -------
        >>> from msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        >>> from msnm.modules.ma import mspc

        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov_mspc.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        >>> weights = np.ones((x.shape[0],1))
          
        >>> # data preprocess auto-scaled
        >>> xcs, average, scale = tools.preprocess2D(x,2,weights)
          
        >>> #PCA
        >>> pcaModel = pca.PCA()
        >>> pcaModel.setPCs(1) # like in mspc.m example
        >>> pcaModel.setData(xcs)
        >>> pcaModel.runPCA()
          
        >>> T = pcaModel.getScores()
        >>> P = pcaModel.getLoadings()
          
        >>> # anomalous data test
        >>> test = data['test']
          
        >>> # data test autoscaled
        >>> testcs = tools.preprocess2Dapp(test,average,scale)
        
        >>> # Computes the Q-statistics
        >>> mspcInstance = mspc.MSPC()
        >>> mspcInstance.computeDst(testcs,P,T)
        
        >>> Get the result
        >>> Dst = mspcInstance.getDst()
        >>> print Dst
                                    
        """
        
        method_name = "computeDst()"
        
        try:
            #new scores from testcs and the loadings (R) of the calibration model
            t = np.dot(testcs,P)        
            
            #inverse of the model calibration scores (T)
            #Note: inv() method just allows at least 2D arrays 
            t_cov = np.cov(T,rowvar=False)
            
            try:
                invCT = np.linalg.inv(t_cov)
            except LinAlgError:
                invCT = 1 / t_cov            
            
    #         if all(t_cov.shape):# True the shape tuple is empty
    #             # When T has only one variable -> cov(T) computes the variance
    #             invCT = 1 / t_cov
    #         else:    
    #             invCT = np.linalg.inv(t_cov)            
                
            dotAux = np.dot(t,invCT)
           
            # Computes D-statistics from the observations in testcs
            self._Dst = np.sum(np.multiply(dotAux,t),axis=1).reshape(testcs.shape[0],1);
            
            # Check is the statistic is and ndarray of [1x1] dimensions and get the float value
            if isinstance(self._Dst, np.ndarray):
                self._Dst = self._Dst[0,0]
            
            # TODO: Sometimes after computations numpy takes UCLq as complex with 0j imaginary part
            if isinstance(self._Dst, complex):
                logging.warn("Dst has a complex value of %s. Getting just the real part.",self._Dst)
                self._Dst = self._Dst.real
        
        except Exception:
            raise MSPCError(self,sys.exc_info()[0], method_name)
        
    def computeoMEDA(self, testcs, dummy, P):
        """Computes oMEDA diagnostic for finding anomalous variables. Set the ``self._oMEDA`` as a result
        
        Observation-based Missing data methods for Exploratory Data Analysis 
        (oMEDA). The original paper is Journal of Chemometrics, 2011, 25 
        (11): 592-600. This algorithm follows the direct computation for
        Known Data Regression (KDR) missing data imputation.
        
        .. [Ref] Observation-based missing data methods for exploratory data analysis to unveil the connection between observations and variables in latent subspace models
            http://onlinelibrary.wiley.com/doi/10.1002/cem.1405/abstract
        
        Parameters
        ----------        
        testcs: numpy.ndarray
            [NxM] preprocessed billinear data set with the observations to be monitored.
        dummy: numpy.ndarray
            [Nx1] dummy variable containing weights for the observations to compare, and 0 for the rest of observations.
        P: numpy.ndarray 
            [MxA] Matrix to perform the projection from the original to the latent subspace. 
            For PCA (testcs = T*P'), this is the matrix of loadings
            
        Raises
        ------
        MSPCError
            When something is going wrong during the mathematical operations
            
        Example
        -------
        >>> from msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        >>> from msnm.modules.ma import mspc
        
        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov_omeda.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        >>> weights = np.ones((x.shape[0],1))
          
        >>> # data preprocess auto-scaled
        >>> xcs, average, scale = tools.preprocess2D(x,2,weights)
          
        >>> #PCA
        >>> pcaModel = pca.PCA()
        >>> pcaModel.setPCs(1) # like in mspc.m example
        >>> pcaModel.setData(xcs)
        >>> pcaModel.runPCA()
          
        >>> T = pcaModel.getScores()
        >>> P = pcaModel.getLoadings()
          
        >>> # anomalous data test
        >>> test = data['test']
          
        >>> # dummy
        >>> dummy = np.zeros((1,10))
        >>> dummy[0,0] = 1
  
        >>> # data test autoscaled
        >>> testcs = tools.preprocess2Dapp(test,average,scale)
        
        >>> # Computes oMEDA
        >>> mspcInstance = mspc.MSPC()
        >>> mspcInstance.computeoMEDA(testcs,dummy,P)
        
        >>> # Gets oMEDA vector
        >>> oMEDAvector = mspcInstance.getoMEDAvector()
        >>> print oMEDAvector
                                    
        """
        
        method_name = "computeoMEDA()"
        
        try:
        
            if dummy.shape[0] == 1:
                dummy = dummy.T
                            
            # To normalice the dummy vector [-1, 1]
            if dummy[dummy > 0].size != 0:
                dummy[dummy > 0] = dummy[dummy > 0] / np.max(dummy[dummy > 0])
            if dummy[dummy < 0].size != 0:
                dummy[dummy < 0] = (dummy[dummy < 0] / np.min(dummy[dummy < 0]))*(-1)
                  
            xA = np.dot(np.dot(testcs,P),P.T);   
            sumA = np.dot(xA.T,dummy);       
            sumTotal = np.dot(testcs.T,dummy);        
            
            self._oMEDA = ((2*sumTotal - sumA)*np.abs(sumA)) / np.sqrt(np.dot(dummy.T,dummy))
        
        except Exception:
            raise MSPCError(self,sys.exc_info()[0], method_name)
        
        
        
    def computeUCLD(self,npc,nob,p_value,phase):
        """
        UCL (Upper Control Limit) for D-statistic
        
        .. [Ref] PCA-based multivariate statistical network monitoring for anomaly detection
            http://www.sciencedirect.com/science/article/pii/S0167404816300116
        
        Parameters
        ----------
        npc: int 
            Number of PCs
        nob: int 
            Number of observations
        p_value: float 
            p-value of the test, in (0,1]
        phase: int 
            SPC phase
            1: Phase I
            2: Phase II
            
        Return
        ------
        lim: float64
            control limit at a 1-``p_value`` confidence level.
            
        Raises
        ------
        MSPCError
            When something is going wrong during the mathematical operations
            
        Examples
        --------
        >>> from msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        >>> from msnm.modules.ma import mspc

        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov_mspc.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        >>> weights = np.ones((x.shape[0],1))
          
        >>> # data preprocess auto-scaled
        >>> xcs, average, scale = tools.preprocess2D(x,2,weights)
          
        >>> #PCA
        >>> pcaModel = pca.PCA()
        >>> pcaModel.setPCs(1) # like in mspc.m example
        >>> pcaModel.setData(xcs)
        >>> pcaModel.runPCA()
          
        >>> T = pcaModel.getScores()
        >>> P = pcaModel.getLoadings()
        
        >>> # Compute UCLs
        >>> mspcInstance = mspc.MSPC()
        >>> # Number of observations
        >>> nob = x.shape[0]
        >>> # Compute UCL for D-statistics with 95% of confidence level
        >>> mspcInstance.computeUCLD(npcs, nob, 0.05, 2)
        
        >>> print "UCLd --> %f" % mspcInstance.getUCLD()
        
        """
        
        method_name = "computeUCLD()"
        
        try:
        
            if phase == 2:
                lim = (npc*(nob*nob-1.0)/(nob*(nob-npc)))*fisher.ppf(1-p_value,npc,nob-npc)
            else:
                lim = (nob-1.0)**2/nob*beta.ppf(1-p_value,npc/2.0,(nob-npc-1)/2.0)
            
            # Check is the limit is and ndarray of [1x1] dimensions and get the float value
            if isinstance(lim, np.ndarray):
                lim = lim[0,0]
            
            # TODO: Sometimes after computations numpy takes UCLq as complex with 0j imaginary part
            if isinstance(lim, complex):
                logging.warn("UCLd has a complex value of %s. Getting just the real part.",lim)
                lim = lim.real
            
            self._UCLD = lim
        
        except Exception:
            raise MSPCError(self,sys.exc_info()[0], method_name)
        
    def computeUCLQ(self,res,p_value):
        """
        UCL (Upper Control Limit) for Q-statistic
        
        .. [Ref] Control Procedures for Residuals Associated With Principal Component Analysis
            http://www.tandfonline.com/doi/abs/10.1080/00401706.1979.10489779
        
        Parameters
        ----------
        res: numpy.ndarray 
            [NxM] Two-way residuals data matrix
        p_value: float 
            p-value of the test, in (0,1]       
            
        Return
        ------
        lim: float64
            control limit at a 1-``p_value`` confidence level.
            
        Raises
        ------
        MSPCError
            When something is going wrong during the mathematical operations
            
        Examples
        --------
        >>> from msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        >>> from msnm.modules.ma import mspc

        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov_mspc.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        >>> weights = np.ones((x.shape[0],1))
          
        >>> # data preprocess auto-scaled
        >>> xcs, average, scale = tools.preprocess2D(x,2,weights)
          
        >>> #PCA
        >>> pcaModel = pca.PCA()
        >>> pcaModel.setPCs(1) # like in mspc.m example
        >>> pcaModel.setData(xcs)
        >>> pcaModel.runPCA()
          
        >>> T = pcaModel.getScores()
        >>> P = pcaModel.getLoadings()
        
        >>> # Compute UCLs
        >>> mspcInstance = mspc.MSPC()       
        >>> # Compute UCL for Q-statistics with 99% of confidence level
        >>> E = xcs - np.dot(T,P.T)
        >>> mspcInstance.computeUCLQ(E, 0.01)
        
        >>> print "UCLq --> %f" % mspcInstance.getUCLQ()
        
        """
        
        method_name = "computeUCLQ()"
        
        try:
                
            # Rows of E matrix
            N = res.shape[0]
            
            # rank of E
            pcs_left = np.linalg.matrix_rank(res);
    
            #
            lambda_eig = np.linalg.eigvals((1.0/(N-1))*np.dot(res.T,res))
            # Get the DESC order according to the ABS value of eigenvalues
            lambda_eig = lambda_eig[np.abs(lambda_eig).argsort()[::-1]]        
    
            theta1 = np.sum(lambda_eig[:pcs_left])
            theta2 = np.sum(lambda_eig[:pcs_left]**2)
            theta3 = np.sum(lambda_eig[:pcs_left]**3)
    
            h0 = 1-((2*theta1*theta3)/(3*theta2**2))
    
            z = norm.ppf(1-p_value)
    
            UCLq = theta1*((z*np.sqrt(2*theta2*(h0**2))/theta1) + 1 + (theta2*h0*(h0-1)/(theta1**2)))**(1/h0)
            
            # Check is the limit is and ndarray of [1x1] dimensions and get the float value
            if isinstance(UCLq, np.ndarray):
                UCLq = UCLq[0,0]
                
            # TODO: Sometimes after computations numpy takes UCLq as complex with 0j imaginary part
            if isinstance(UCLq, complex):
                logging.warn("UCLq has a complex value of %s. Getting just the real part.",UCLq)
                UCLq = UCLq.real
                            
            self._UCLQ = UCLq
        
        except Exception:
            raise MSPCError(self,sys.exc_info()[0], method_name)
        
        
        
    # Getter and Setter methods
    def getQst(self):       
        return self._Qst
        
    def getDst(self):
        return self._Dst
    
    def getUCLQ(self):
        return self._UCLQ
    
    def getUCLD(self):
        return self._UCLD
        
    def getoMEDAvector(self):
        return self._oMEDA
        
        
        
    