# -*- coding: utf-8 -*-
"""
    :mod:`Error definitions module`
    ===========================================================================
    :synopsis: Contains the description and definitios of every kind of error (exception) that could be raised
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""
class MSNMError(Exception):
    """

    *General error definition*

    Attributes
    ----------
    _obj: object
        instance of the class which raises the exception
    _msg: str
        error message
    _method: str
        method name where the error is raised

    See Also
    --------
    Exception
    """

    def __init__(self, obj, message='',method=''):
        self._obj = obj
        self._msg = message
        self._method = method

    def print_error(self):
        """
            Print the error in a specific format
        """

        if not self._obj:
            object_class = ''
        else:
            object_class = self._obj.__class__

        print("ERROR: %s, Type: %s, Method: %s" %(self._msg,object_class,self._method))

    def get_msg(self):
        return self._msg

    def get_method(self):
        return self._method

    def get_obj(self):
        return self._obj

class DataSourceError(MSNMError):
    """
    *Error definition related to the data sources modules/classes*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class SensorError(MSNMError):
    """
    *Error definition related to the sensor module*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class ModelError(MSNMError):
    """
    *Error definition related to the model module*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class PCAError(MSNMError):
    """
    *Error definition related to the PCA module*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class MSPCError(MSNMError):
    """
    *Error definition related to the MSPC module*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class ConfigError(MSNMError):
    """
    *Error definition related to the configuration issues*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class CommError(MSNMError):
    """
    *Error definition related to the communication issues*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass

class DTableError(MSNMError):
    """
    *Error definition related to the diagnostic table issues*

    See Also
    --------
    msnm.exceptions.MSNMError
    """
    pass
