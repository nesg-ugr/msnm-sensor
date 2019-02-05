# -*- coding: utf-8 -*-

"""
    :mod:`PCA module`
    ===========================================================================
    :synopsis: PCA (Principal Component Analysis)
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

import numpy.linalg as linalg
import numpy as np
import sys
from numpy.linalg.linalg import LinAlgError
from msnm.exceptions.msnm_exception import PCAError

class PCA:
    """
        
    *PCA (Principal Component Analysis) container*. It contains the basic methods to compute PCA through
    SVD (Singular Value Decomposition) analysis.
        
    Attributes
    ----------
    _data: numpy.ndarray 
        [NxM] preprocessed billinear data set
    _pcs: int
        number of PCs (Principal Components)
    _scoresMatrix: numpy.ndarray
        T [NxA] scores matrix of X = T*P'
    _loadingsMatrix: numpy.ndarray 
        P [MxA] loadings matrix of X = T*P'
    _residualsMatrix: numpy.ndarray
        E [NxM] residuals matrix of E = X - T*P'
    _model: numpy.ndarray
        X [NxM] matrix from X = T*P'
    _eigengvaluesMatrix: numpy.ndarray
        [AxA] diagonal matrix of eigenvalues
         
    See Also
    --------
    msnm.model
    msnm.utils
    numpy.linalg
    """      

    def __init__(self):       
        self._data = 0
        self._pcs = 0
        self._scoresMatrix = 0
        self._loadingsMatrix = 0
        self._residualsMatrix = 0
        self._model = 0
        self._eigengvaluesMatrix = 0                
        
    def runPCA(self, method='svd', **kwargs):
        """PCA (Principal Component Analysis)
        
        Computes PCA and sets ``self._scoresMatrix``, ``self._loadingMatrix`` and ``self._residualsMatriz`` among others
        
        Parameters
        ----------
        method: str 
            Choose the inner method to process PCA:
               'svd': SVD 
               'eig': through getting the eigenvectors and eigenvalues from the X'*X
        xxcrossdata (optional): numpy.ndarray
            When 'eig' method is selected, the cross-product X'*X comes from this input parameter. Otherwise, X'*X will be computed inside.
        
        Raises
        ------
        PCAError            
            
        Example
        -------
        >>> from examples.scenario_4.routerR1.msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        
        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov.mat'
          
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
        >>> pcaModel.runPCA('svd')
          
        >>> T = pcaModel.getScores()
        >>> P = pcaModel.getLoadings()
        >>> E = pcaModel.getResiduals()                                    
        """      
        
        method_name = "runPCA()"
        
        try:        
            if method == 'svd':
            
                # Run SVD from the data matrix
                u, s, v = self.runSVD(self._data)
                            
                # Compute T and P matrix. 
                # NOTE that P matrix is V' when this is computed from numpy library
                t = np.dot(u, s)            
                p = v.T
            
            elif method == 'eig':
                if 'xxcrossdata' not in kwargs:
                    # Computing cross-product
                    XX = np.dot(self._data.T,self._data)
                else:
                    XX = kwargs['xxcrossdata']                
                    
                # s, eigenvalues
                # p, eigenvectors
                s,p = linalg.eig(XX)
                
                # Sort the eigenvectors their corresponding eigenvalue
                ind = np.argsort(s)[::-1]# get the indexes in descending order
                p = p[:,ind]# get the complete P matrix
                # get the complete score matrix
                t = np.dot(self._data, p)
            
        except LinAlgError:
                raise PCAError(self,sys.exc_info()[1], method_name)                                    
        
        self._scoresMatrix = t[:, :self._pcs]
        self._loadingsMatrix = p[:, :self._pcs]
        self._model = np.dot(self._scoresMatrix, self._loadingsMatrix.T)
        self._residualsMatrix = self._data - self._model
        self._eigengvaluesMatrix = s
        
    @staticmethod
    def runPCADirect(data, pcs):
        """PCA (Principal Component Analysis) based on SVD (Singular Value Decomposition).
         
        This method obtains the PCA model like in ``runPCA()`` method.
        
        .. note::
            This method is devised to be invoked directly without any instance
        
        Parameters
        ----------
        data: numpy.ndarray 
            [NxM] preprocessed billinear data set
        pcs: int
            number of PCs (Principal Components)
            
        Return
        ------
        scoresMatrix: numpy.ndarray
            T [NxA] scores matrix of X = T*P'
        loadingsMatrix: numpy.ndarray 
            P [MxA] loadings matrix of X = T*P'
        residualsMatrix: numpy.ndarray
            E [NxM] residuals matrix of E = X - T*P'
        model: numpy.ndarray
            X [NxM] matrix from X = T*P'
            
        Raises
        ------
        PCAError
            When SVD method does not converge
            
        Example
        -------
        >>> from examples.scenario_4.routerR1.msnm.utils import datautils as tools
        >>> import numpy as np
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        
        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        >>> weights = np.ones((x.shape[0],1))
          
        >>> # data preprocess auto-scaled
        >>> xcs, average, scale = tools.preprocess2D(x,2,weights)
        
        >>> T, P, X, E = pca.PCA.runPCADirect(xcs,pcs = 3)                                             
        """  
        
        method_name = "runPCADirect()"
        
        try:    
            # Run SVD from the data matrix
            # NOTE: this is the way of to call static methods within the class
            u, s, v = PCA.runSVD(data)
        except LinAlgError as e:
            raise PCAError(self,e.msg, method_name)
        
        # Compute T and P matrix. 
        # NOTE that P matrix is V' when this is computed from numpy library
        t = np.dot(u, s)
        p = v.T
        
        scoresMatrix = t[:, :pcs]
        loadingsMatrix = p[:, :pcs]
        model = np.dot(scoresMatrix, loadingsMatrix.T)
        residualsMatrix = data - model        
        
        return scoresMatrix, loadingsMatrix, model, residualsMatrix
        
    @classmethod
    def runSVD(self, data):
        """SVD (Singular Value Decomposition).                
        
        Parameters
        ----------
        data: numpy.ndarray 
            [NxM] preprocessed billinear data set
            
        Return
        ------
        u: numpy.ndarray
            [NxN] unitary matrix
        s: numpy.ndarray
            [NxM] diagonal matrix containing the eigenvalues of ``data``
        v: numpy.ndarray
            [MxN] unitary matrix
            
        Raises
        ------
        LingAlgError
            When SVD method does not converge
            
        Example
        -------
        >>> import scipy.io as sio
        >>> from msnm.modules.ma import pca
        
        >>> # Original data (complete workspace of matlab example in mspc.m of MEDA)
        >>> originalData = './datatest/data_adicov.mat'
          
        >>> # Calibration matrix
        >>> data = sio.loadmat(originalData)
        >>> x = data['X']
        
        >>> pcaModel = pca.PCA()
        >>> U,S,V = pcaModel.runSVD(xcs)                                             
        """
        
        # Run SVD from the data matrix
        u, s, v = linalg.svd(data)

        # Transform S from array to matrix with the corresponding dimensions
        # in U and V
        sdiag = np.diag(s)
        s = np.zeros((u.shape[1], v.shape[0]))
        s[:sdiag.shape[0], :sdiag.shape[1]] = sdiag        
        
        return u, s, v
        
    ### Setter and Getter methods
    def setData(self, data):
        self._data = data        
        
    def setPCs(self, pcs):
        self._pcs = pcs

    def getScores(self):
        return  self._scoresMatrix
        
    def getLoadings(self):
        return self._loadingsMatrix
    
    def getEigenvalues(self):
        return self._eigengvaluesMatrix
    
    def getModel(self):
        return self._model
    
    def getResidual(self):
        return self._residualsMatrix
   
            
        
        
