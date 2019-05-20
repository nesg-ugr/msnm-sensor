# -*- coding: utf-8 -*-
"""
    :mod:`Data utilities`
    ===========================================================================
    :synopsis: Several methods to play with data
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

import numpy as np
import pandas as pd
import sys
import logging
from msnm.exceptions.msnm_exception import MSNMError
from collections import OrderedDict
import json
import scipy.io as sio
from msnm.modules.ma.pca import PCA
from msnm.modules.ma.mspc import MSPC
from msnm.modules.config.configure import Configure
from msnm.modules.source.source import Source

def preprocess2D(x, prep, weights):
    """
    Data preprocessing depending on ``prep`` parameter

    Parameters
    ----------
    x: numpy.ndarray
        [NxM] billinear data set
    prep: int
        Choose the preprocessing method:
           0: no preprocessing
           1: mean-centering
           2: auto-scaling (default)
    weights: numpy.ndarray
        [1xM] weight applied after preprocessing. Set to a vector of 1s by defect.

    Return
    ------
    xcs: numpy.ndarray
        [NxM] preprocessed data.
    average: numpy.ndarray
        [1xM] sample average according to the preprocessing method.
    scale: numpy.ndarray
        [1xM] sample scale according to the preprocessing method.

    .. todo::
        weights vector is not implemented

    Raises
    ------
    MSNMError
        General error is when something was wrong

    Example
    -------
    >>> from msnm.utils import datautils as tools
    >>> import numpy as np
    >>> import scipy.io as sio

    >>> # Original data set X
    >>> originalData = './datatest/data_adicov_mspc.mat'

    >>> # Returns a dictonary like {'variable_name':'variable_data'}
    >>> x = sio.loadmat(originalData)
    >>> data = x['X']
    >>> weights = np.ones((data.shape[0],1))
    >>> xcs, average, scale = tools.preprocess2D(data,2,weights)
    """

    method_name = "preprocess_2D()"

    try:

        if prep == 1:
            # mean avoiding NaN for each variable
            average = np.nanmean(x,axis=0)# array of M elements
            average = average.reshape((1,average.shape[0]))# Matrix of 1xM elements
            # array 1xM, being M the number of variables
            scale = np.ones((1,x.shape[1]))
            # substract the average to the data set x
            xcs = x - np.dot(np.ones((x.shape[0],1)),average)
            # TODO: do test with NaN in the data set

        elif prep == 2:

            # not a numbers and a number in X
            nanM = np.isnan(x)
            anM = 1 - nanM

            average = np.nanmean(x,axis=0)# array of M elements
            average = average.reshape((1,average.shape[0]))# Matrix of 1xM elements
            scale = np.nanstd(x,axis=0,ddof=1)

            #TODO: to ask Pepe what is this :(
            ind = np.nonzero(scale == 0)# # of zeroes in scale
            dem = 2.0*np.sum(anM[:,ind],axis=0) - 1
            scale[ind] = np.sqrt(np.ones((1,np.array(ind).size)) / dem)

            scale = scale.reshape((1,scale.shape[0]))# Matrix of 1xM elements
            xcs = x - np.dot(np.ones((x.shape[0],1)),average)
            xcs = xcs / np.dot(np.ones((x.shape[0],1)),scale)
            # TODO: do test with NaN in the data set

        else:
            logging.warn("Preprocessing method %s is not available ...", prep)

    except Exception:
        raise MSNMError(None,sys.exc_info()[0],method_name)

    return xcs, average, scale

def preprocess2Dapp(test, average, scale):
    """
    Apply autoscaled preprocessing to ``test`` data

    Parameters
    ----------
    test: numpy.ndarray
        [NxM] billinear data set
    average: numpy.ndarray
        [1xM] sample average to substract
    scale: numpy.ndarray
        [1xM] sample scale to divide the test

    Return
    ------
    testAutoScaled: numpy.ndarray
        [NxM] preprocessed data.

    Raises
    ------
    MSNMError
        General error is something is wrong

    Example
    -------
    >>> from msnm.utils import datautils as tools
    >>> import numpy as np
    >>> import scipy.io as sio

    >>> # Original data set X
    >>> originalData = './datatest/data_adicov_mspc.mat'

    >>> # Returns a dictonary like {'variable_name':'variable_data'}
    >>> x = sio.loadmat(originalData)
    >>> data = x['X']
    >>> weights = np.ones((data.shape[0],1))
    >>> xcs, average, scale = tools.preprocess2D(data,2,weights)
    >>> # anomalous data test
    >>> test = data['test']

    >>> # data test autoscaled
    >>> testcs = tools.preprocess2Dapp(test,average,scale)
    """

    method_name = "preprocess2Dapp()"

    try:

        # mean centering
        testMeanCenterting = test - np.dot(np.ones((test.shape[0],1)),average)

        # auto-scaled
        testAutoScaled = testMeanCenterting / (np.dot(np.ones((test.shape[0],1)),scale))

    except Exception:
        raise MSNMError(None,sys.exc_info()[0],method_name)

    return testAutoScaled

def preprocess2Di(x, prep, lamda, average, scale, N, weights):
    """
    Data preprocessing applying EWMA methodology.

    J. Camacho, “Visualizing Big data with Compressed Score Plots: Approach and research challenges,”
    Chemometrics and Intelligent Laboratory Systems, vol. 135, pp. 110–125, Jul. 2014.

    References
    ----------
    Visualizing Big data with Compressed Score Plots: Approach and research challenges
    http://www.sciencedirect.com/science/article/pii/S016974391400080X

    Parameters
    ----------
    x: numpy.ndarray
        [NxM] billinear data set
    prep: int
        Choose the preprocessing method:
           0: no preprocessing
           1: mean-centering
           2: auto-scaling (default)
    lamda: float
        forgetting factor [0,1]
    average: numpy.ndarray or scalar
        [1xM] (t-1) previous computed average array
    scale: numpy.ndarray or scalar
        [1xM] (t-1) previous computed scale array
    N: int
        number of observations used to compute mean and scale vectors
    weights: numpy.ndarray
        [1xM] weight applied after preprocessing. Set to a vector of 1s by defect.

    Return
    ------
    xcs: numpy.ndarray
        [NxM] preprocessed data.
    average: numpy.ndarray
        [1xM] sample average according to the preprocessing method.
    scale: numpy.ndarray
        [1xM] sample scale according to the preprocessing method.
    N: int
        Current N after applying the forgetting factor

    .. todo::
        weights vector is not implemented yet

    Raises
    ------
    MSNMError
        General error is when something was wrong

    Example
    -------
    >>> from msnm.utils import datautils as tools
    >>> import numpy as np
    >>> import scipy.io as sio

    >>> # Original data set X
    >>> originalData = './datatest/data_adicov_mspc.mat'

    >>> # Returns a dictonary like {'variable_name':'variable_data'}
    >>> x = sio.loadmat(originalData)
    >>> data = x['X']
    >>> weights = np.ones((data.shape[0],1))
    >>> xcs, average, scale = tools.preprocess2D(data,2,weights)
    """

    method_name = "preprocess_2D()"

    logging.info("Preprocessing data dynamically for N=%s obs and lambda=%s",N,lamda)

    # EWMA mean update model
    # M_t^x = lambda * M_(t-1)^x + X_t
    # m_t^x = (1/N_t) * M_t^x
    # N_t = lambda * N_(t-1) + B_t

    # acc <=> M_t^x --> Current model accumulated
    # average <=> m_t^x --> Current model mean
    acc = average*N;

    # acc2 <=> (sigma_t^x)^2 --> Current model variability accumulated
    # scale <=> sigma_t^x --> Current model standard deviation
    acc2 = (scale**2)*np.max([N-1,0]);

    # Current number of real observations to compute the mean and standard
    # deviation
    N = lamda*N + x.shape[0];

    try:

        if prep == 1:# mean centering

            logging.debug("EWMA mean centering")

            # Computes the current model mean
            acc = lamda*acc + np.sum(x, axis=0)
            average = acc/N
            average = average.reshape(1,x.shape[1])
            # array 1xM, being M the number of variables.
            scale = np.ones((1,x.shape[1]))
            # subtract the average to the data set x
            xcs = x - np.dot(np.ones((x.shape[0],1)),average)

            # TODO: do test with NaN in the data set

        elif prep == 2: # auto-scaling
            logging.debug("EWMA auto-scaling")

            # Computes the current model mean
            acc = lamda*acc + np.sum(x, axis=0)
            average = acc/N;
            average = average.reshape(1,x.shape[1])

            # subtract the average to the data set x
            xc = x - np.dot(np.ones((x.shape[0],1)),average)
            # Computes the current model standard deviation
            acc2 = lamda*acc2 + np.sum(xc**2,axis=0)
            scale = np.sqrt(acc2/(N-1))

            # scale is all of zeros?
            if np.nonzero(scale)[0].shape[0] == 0:
                mS = 2
            else:
                mS = np.min(scale[np.nonzero(scale)])

            scale[np.nonzero(scale == 0)] = mS/2# use 1 by default may reduce detection of anomalous events
            # apply the scale
            scale = scale.reshape(1,x.shape[1])
            xcs = xc / np.dot(np.ones((x.shape[0],1)),scale)

            # TODO: do test with NaN in the data set

        elif prep == 3:
            logging.debug("EWMA scaling")

            # Computes the current model mean
            average = np.zeros((1,x.shape[1]))

            # Computes the current model standard deviation
            acc2 = lamda*acc2 + np.sum(x**2,axis=0)
            scale = np.sqrt(acc2/(N-1))

            # scale is all of zeros?
            if np.nonzero(scale)[0].shape[0] == 0:
                mS = 2
            else:
                mS = np.min(scale[np.nonzero(scale)])

            scale[np.nonzero(scale == 0)] = mS/2# use 1 by default may reduce detection of anomalous events
            # apply the scale
            scale = scale.reshape(1,x.shape[1])
            xcs = x / np.dot(np.ones((x.shape[0],1)),scale)

            # TODO: do test with NaN in the data set

        else:
            logging.warn("The selected preprocessing method is not valid")
            average = np.zeros((1,x.shape[1]))
            scale = np.ones((1,x.shape[1]))
            xcs = x

    except Exception:
        logging.error("Error preprocessing the data: %s",sys.exc_info()[1])
        raise MSNMError(None,sys.exc_info()[1],method_name)

    return xcs, average, scale, N


def zeroDataImputation(**kwargs):

    method_name = "zeroDataImputation()"

    # Check optional parameters
    if 'obs' in kwargs:
        obs = kwargs['obs']
    else:
        logging.error("There is no observation to recover")
        msnmerror = MSNMError(None,"There is no observation to recover",method_name)
        raise msnmerror

    #Zero value imputation
    logging.debug("Doing zero based data imputation ...")
    rec_obs = pd.DataFrame(obs).fillna(0).as_matrix()

    return rec_obs

def averageDataImputation(**kwargs):
    """
    All missing data in X (NxM) will be replaced by their
    average value
    """

    method_name = "averageDataImputation()"

    # Check optional parameters
    # Check the observation for imputation
    if 'obs' in kwargs:
        obs = kwargs['obs']
    else:
        logging.error("There is no observation to recover")
        msnmerror = MSNMError(None,"There is no observation to recover",method_name)
        raise msnmerror
    # Check the calibration model
    if 'model' in kwargs:
        model = kwargs['model']
    else:
        logging.error("There is no calibration model")
        msnmerror = MSNMError(None,"There is no calibration model",method_name)
        raise msnmerror

    #Doing average imputation
    logging.debug("Doing average based data imputation ...")
    rec_obs = pd.DataFrame(obs).fillna(pd.DataFrame(model.get_av())).as_matrix()

    return rec_obs


def sort_vector(vector, order, axis, abs_value):

    method_name = "sort_vector()"

    # Check the data type as ndarray
    if not isinstance(vector, np.ndarray):
        raise MSNMError(None,"Data is not an ndarray",method_name)

    try:

        # Absolute value?
        if abs_value:
            aux = np.abs(vector)
        else:
            aux = vector

        # Sorting asc
        aux = np.sort(aux,axis=axis)

        # Do sorting desc?
        if order == 'desc':
            aux = aux[::-1]

    except Exception:
        raise MSNMError(None,sys.exc_info()[0],method_name)

    return aux

def sort_dict(keys,values,order_by,order,abs_value):
    #TODO: check keywords parameters

    method_name = "sort_dict()"

    # Check the data type as dict
    if not isinstance(keys, list):
        raise MSNMError(None,"Invalid list of keys", method_name)

    # Check the data type as ndarray
    if not isinstance(values, np.ndarray):
        raise MSNMError(None,"Invalid values array", method_name)

    try:
        # Absolute value?
        if abs_value:
            aux = np.abs(values)
        else:
            aux = values

        # Which order?
        if order == 'desc':
            reverse_order = True
        else:
            reverse_order = False

        # Make a dict from {keys:values}
        d = dict(zip(keys,aux))

        if order_by == 'key':
            d = OrderedDict(sorted(d.items(),key=lambda t: t[0],reverse=reverse_order))
        else:
            d = OrderedDict(sorted(d.items(),key=lambda t: t[1],reverse=reverse_order))

    except Exception:
        raise MSNMError(None,sys.exc_info()[0],method_name)

    return d


def sort_dictionary(dictionary,order_by='key',order='desc'):
    #TODO: check keywords parameters

    method_name = "sort_dictionary()"

    logging.info("Sorting dict ...")

    # Check the data type as dict
    if not isinstance(dictionary, dict):
        raise MSNMError(None,"Invalid dict as param", method_name)

    try:

        # Which order?
        if order == 'desc':
            reverse_order = True
        else:
            reverse_order = False

        if order_by == 'key':
            d = OrderedDict(sorted(dictionary.items(),key=lambda t: t[0],reverse=reverse_order))
        else:
            d = OrderedDict(sorted(dictionary.items(),key=lambda t: t[1],reverse=reverse_order))

    except Exception:
        raise MSNMError(None,sys.exc_info()[0],method_name)

    logging.info("Ending sorting dict ...")

    return d


def model2json(model,ts):
    """
    Build a json object from a model object (See Model class for more information):

    Parameters
    ----------
    model: msnm.modules.ma.model
        Model containing a lot of paramenters
    ts: str
        Model saving timestamp
        
    Example
    -------
    {
    "_alpha": 0.05,
    "_av": 0.0,
    "_data": 0.0,
    "_dataxcs": 0.0,
    "_lv": 3,
    "_mspc": {
    "_Dst": 0.0,
    "_Qst": 0.0,
    "_UCLD": 0.0,
    "_UCLQ": 0.0,
    "_oMEDA": 0.0
    },
    "_pca": {
    "_data": 0,
    "_eigengvaluesMatrix": 0,
    "_loadingsMatrix": 0,
    "_model": 0,
    "_pcs": 0,
    "_residualsMatrix": 0,
    "_scoresMatrix": 0
    },
    "_phase": 2,
    "_prep": 2,
    "_sd": 0.0
    }

    """

    logging.info("Packaging model json format.")

    # Add ts to the backup
    model.__dict__.update({'_ts':ts})

    # Model to json
    json_model = json.dumps(model.__dict__,cls=MSNMJsonEncoder,indent=4,sort_keys=True)

    return json_model

def save2json(json_contents, path_to_save):

    logging.info("Saving json file in %s", path_to_save)

    try:
        with open(path_to_save,'w') as f:
            # Save raw data
            f.writelines(json_contents)
    except IOError as ioe:
        logging.error("Error saving json file: %s",sys.exc_info()[1])
        raise MSNMError(ioe, sys.exc_info()[1], 'save2json()')

def json2mat(input_json_path, output_mat_path, json_field):

    """
    Extract a field from a JSON file in \*.mat format to be afterwards used in Matlab or Octave
    """

    with open(input_json_path,'r') as f:
        json_file = json.load(f)

    for key in json_file.keys():
        # Remove '_' character from the json_field name at the beginning
        if key[0] == '_': key_new = key[1:]
        # Replace keys without '_' character
        json_file[key_new] = json_file.pop(key)

    if json_field[0] == '_': json_field_new = json_field[1:]

    # Save file
    sio.savemat(output_mat_path, {json_field_new: json_file[json_field_new]})


def getVarNamesFromSource(source_config):

    """
    Get the variables name from the flow parser configuration file of each data sources.
    TODO: right only accepts local sources but should we to extend it for remote sources?
    
    Parameters
    ----------
    source_config: dict
        Data type for finding variables in specific data source
        

    Example
    -------

    >>> source_config = config.get_config()['DataSources']['local']['IPTables']['parserContents']
    >>> getVarNamesFromSource(source_config)

    """

    var_list = []

    for i in source_config[Source.S_VARIABLES]:
        var_list.append(i['name'])

    return var_list


def getAllVarNames():

    """
    Concatenates all variable names from all data source

    """

    # Config params
    config = Configure()

    local_sources_vars_names = []
    remote_sources_vars_names = []

    try:
        local_sources = config.get_config()['DataSources']['local']

        # Get local sources var names
        for i_local in local_sources:
            local_sources_vars_names.extend(getVarNamesFromSource(local_sources[i_local]['parserContents']))

    except KeyError as ke:
            logging.warning("There are no local sources configured: %s", ke)

    try:
        remote_sources = config.get_config()['DataSources']['remote']

        # Get remote sources var names
        for i_remote in remote_sources:
            # Right now every remote sources has only two variables Q and D
            # TODO: to extend for more flexibility like in local sources
            remote_sources_vars_names.append('Q_'+ i_remote)
            remote_sources_vars_names.append('D_'+ i_remote)

    except KeyError as ke:
            logging.warning("There are no remote sources configured: %s", ke)

    all_vars = local_sources_vars_names + remote_sources_vars_names
    logging.debug("%s variables found",len(all_vars))

    return all_vars


# Packet utilities
def pack2json(packet):
    """
    Build a json object from a packet

    {
    "header":{
    "id": 1, # id of the packet
    "sid": S1, # id of the source sensor
    "ts": 201609171745, # time stamp just after computing the Q and T statistics from source sensor
    "type": D # type of packet: D (data), R(response) and C(command)
    },
    "body":{
    "Q": 15.45, # Q statistic value from source sensor
    "T": 9,65   # T statistic value from source sensor
    }
    }

    NOTE: depending on which packet we are managing the body contents and fields will change.

    """

    logging.info("Packaging packet with ID %s from sensor %s to json format.",packet._header['id'], packet._header['sid'])

    # Build packet as complete dict
    dheader = {"header":packet._header}
    dbody = {"body":packet._body}
    dheader.update(dbody)

    # sort dict 'desc' by 'keys'
    dpacket = sort_dictionary(dheader)

    # json dumps
    return json.dumps(dpacket,cls=MSNMJsonEncoder, indent=4)


def generateRandomCalObsMatrix(nobs, nvar):
    """
    Random generation of a sensor calibration matrix

    Parameters
    ----------
    nobs: int
        Number of observations (rows)
    nvar: int
        Number of variables (cols)

    Return
    ------
    cal_mat: np.array
        [NxM] calibration matrix

    """
    return np.random.randint(0,1000, size=(nobs, nvar))


def generateCalVarLabels(cal_mat_shape):
    """
    Variables' labels of the calibration matrix

    Parameters
    ----------
    cal_mat_shape: tuple
       Tuple of (N,M) nobs and nvar of the calibration matrix

    Return
    ------
    var_l: list
        ['var_1','var_2',...,'var_M']

    """
    return ["var_" + str(i) for i in range(cal_mat_shape[0])]


def packet2csv(packet):

    # Get header
#     csv_header = "#"
#     for i in packet._header.keys():
#         csv_header = csv_header + packet._header[i] + ","

    # Get body
    # think about more verstile method
    pass

class MSNMJsonEncoder(json.JSONEncoder):
    def default(self, obj):

        if isinstance(obj,np.ndarray):
            obj = obj.tolist()
        elif isinstance(obj,complex):
            obj = str(obj)
        elif isinstance(obj, PCA):
            obj = obj.__dict__
        elif isinstance(obj, MSPC):
            obj = obj.__dict__
        else:
            obj = super(MSNMJsonEncoder, self).default(obj)
        return obj
