# -*- coding: utf-8 -*-

"""
    :mod:`source`
    ===========================================================================
    :synopsis: Represents a general data source
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

from collections import deque
from datetime import datetime
from msnm.modules.config.configure import Configure
from msnm.exceptions.msnm_exception import DataSourceError
from fcparser import fcparser
import sys, traceback
import time
import logging

class Source(object):

    """

    Represents a general data source

    Attributes
    ----------
    _files_generated: dict
        Contains the observation file generated (*.dat) by each data source at a specific timestamp
    _type: str
        Data source type:
            'local': Local source e.g., netflow, iptables, IDS, syslog, etc. that is located in the host where the sensor is deployed
            'remote': Remote source (i.e., remote sensors) from the Q and D statistics are received.

    See Also
    --------
    msnm.modules.source.netflow
    msnm.modules.source.iptables
    """

    # TCP flags formats. Type netflow means that all treated sources will have the same TCP flags as nfdump output
    FORMAT_TCP_FLAGS_NETFLOW_TYPE = "netflow"

    # Source configurations according to the FCParser configuration
    S_VARIABLES = 'FEATURES'

    # Types of sources
    TYPE_L = "local"
    TYPE_R = "remote"

    def __init__(self):
        # TODO: add common attributes among data sources
        self._files_generated = {}
        self._type = self.TYPE_L # Local source by default
        # Configuration
        self.config = Configure()
        # Get root path for creating data files
        self.rootDataPath = self.config.get_config()['GeneralParams']['rootPath']

    def parse(self,file_to_parse):
        """
        Parsing the information from a specific data source

        Parameters
        ----------
        file_to_parse: str
            Path to the file to be parsed

        Raises
        ------
        DataSourceError

        """

        # To be overridden in child classes
        # TODO: it could have a default behavior
        pass

    def start(self):
        """
        This method runs the information gathering of a specific data source

        """
        # To be overridden in child classes
        # TODO: it could have a default behavior
        pass

    def stop(self):
        """
        This method stop the information gathering of a specific data source

        """
        # To be overridden in child classes
        # TODO: it could have a default behavior
        pass

    def format_tcp_flags(self,list_tcp_flags,format_type):
        """
        Normalizing the TCP flags format

        Parameters
        ----------
        list_tcp_flags: list
            TCP flags list in this way: ['ACK','PSH','SYN'] (see iptables module)

        Return
        ------
        formatted_string: str
            A string accordingly formated.

        Example
        -------
        >>> formatted_string = format_tcp_flags(['ACK','PSH','SYN'],format_type=self.FORMAT_TCP_FLAGS_NETFLOW_TYPE)
        >>> print(formatted_string)
        >>> # it should returns '.AP.S.' as nfdump formats the TCP flags


        """
        # TODO: To be extended to another format
        if format_type == self.FORMAT_TCP_FLAGS_NETFLOW_TYPE:
            formatted_string = self.format_tcp_flag_as_netflow(list_tcp_flags)
        else:
            # Default format as netflow
            formatted_string = self.format_tcp_flag_as_netflow(list_tcp_flags)

        return formatted_string

    def format_tcp_flag_as_netflow(self,list_tcp_flags):
        """
        Netflow way to format TCP flags

        Parameters
        ----------
        list_tcp_flags: list
            TCP flags list in this way: ['ACK','PSH','SYN'] (see iptables module)

        Return
        ------
        formatted_string: str
            A string accordingly formated.

        Example
        -------
        >>> formatted_string = format_tcp_flags_as_netflow(['ACK','PSH','SYN'])
        >>> print(formatted_string)
        >>> # it should returns '.AP.S.' as nfdump formats the TCP flags


        """

        # Formatted string of flags
        formatted_string = ""

        for flag in list_tcp_flags:
            if flag:
                formatted_string = formatted_string + flag[0]
            else:
                formatted_string = formatted_string + '.'

        return formatted_string

    def get_file_to_parse(self,file_to_parse, backups_path, nlastlines):
        """
        Obtaining and saving the 'n' last lines of the iptables logs to be parsed.
        Although this method is initially conceived to work with iptables logs it could be
        used with similar log files where

        Parameters
        ----------
        file_to_parse: str
            Path to the whole iptables log file
        backups_path: str
            Path to save the 'n' lines extracted
        nlastlines: int
            The 'n' last lines to be extracted

        Return
        ------
        d:
            A string accordingly formated.

        Example
        -------
        >>> formatted_string = format_tcp_flags_as_netflow(['ACK','PSH','SYN'])
        >>> print(formatted_string)
        >>> # it should returns '.AP.S.' as nfdump formats of the TCP flags


        """

        method_name = "get_file_to_parse()"

        try:

            # Read only the n last lines of the file
            with open(file_to_parse,'r') as f:
                d = deque(f,nlastlines)
                #print d

            # Save the piece of file that is going to be parsed
            with open(backups_path,'w') as fw:
                fw.writelines(list(d))

        except Exception:
            raise DataSourceError(self,sys.exc_info()[0],method_name)

        return d

    def get_file_to_parse_time(self,file_to_parse, timer):
        """
        Getting last lines of specific file during a certain of the iptables logs to be parsed.
        Although this method is initially conceived to work with iptables logs it could be
        used with similar files.

        Parameters
        ----------
        file_to_parse: str
            Path to the whole iptables log file
        backups_path: str
            Path to save the 'n' lines extracted
        nlastlines: int
            The 'n' last lines to be extracted

        Return
        ------
        d:
            A string accordingly formated.

        Example
        -------
        >>> formatted_string = format_tcp_flags_as_netflow(['ACK','PSH','SYN'])
        >>> print(formatted_string)
        >>> # it should returns '.AP.S.' as nfdump formats of the TCP flags


        """

        method_name = "get_file_to_parse_time()"

        try:

            # Log lines gathered from the file
            log_lines = []

            # Read only the n last lines of the file
            with open(file_to_parse,'r') as f:
                # Goes to the end of the file
                f.seek(0,2)
                # Computes the ending time in seconds
                t_end = time.time() + timer
                while time.time() < t_end:
                    line = f.readline()
                    if line:
                        log_lines.append(line)

        except Exception:
            raise DataSourceError(self,sys.exc_info()[0],method_name)

        return log_lines

    def get_synchronized_file(self,df,ts_master_source, sampling_rate):

        config = Configure()
        dateFormat = config.get_config()['GeneralParams']['dateFormat']
        dateFormatNfcapd = config.get_config()['GeneralParams']['dateFormatNfcapdFiles']

        # Format date according the index in the dataframe. Upper timestamp to synchronize
        ts = datetime.strptime(ts_master_source, dateFormatNfcapd)
        end_ts = ts.strftime(dateFormat)

        # Lower timestamp to synchronize: upper timesatemp - samplinr_rate (in minutes)
        init_ts = ts.replace(minute=ts.minute - sampling_rate)
        init_ts = init_ts.strftime(dateFormat)

        # Get the dataframe rows according to the ts_master_source
        return df[str(init_ts):str(end_ts)]

    def get_synchronized_file_from_netflow_dump(self,df,netflow_dumps_path):

        method_name = "get_synchronized_file_from_netflow_dump()"

        try:
            with open(netflow_dumps_path,'r') as f:
                init_ts = f.readline().split(',')[0] # Get the ts of the first line in nfdump *.csv file
                # Get the ts of the last line in nfdump *.csv file
                d = deque(f,1) # Get the las line
                end_ts = list(d)[0].split(',')[0] # Get the ts

        except Exception:
            raise DataSourceError(self,sys.exc_info()[0],method_name)
        # Get the dataframe rows according to the ts_master_source
        return df[str(init_ts):str(end_ts)]

    def launch_flow_parser(self, flow_parser_config):

        """
        Launch the parsing procedure (flow parser)

        Raises
        ------
        MSNMError

        """

        method_name = "launch_flow_parser()"

        #TODO: modify parser source to raise ParseError or some like that as in the MSNM sensor.

        try:
            logging.debug("Parsing from %s configuration.",flow_parser_config)
            fcparser.main(call='internal',configfile=flow_parser_config)
        except Exception:
            logging.error("Error parsing data: %s",sys.exc_info()[2])
            traceback.print_exc()
            raise DataSourceError(self,sys.exc_info()[1],method_name)

    def save_file(self,log_lines,path_to_save):

        method_name = "save_file()"

        try:
            logging.debug("Saving file lines in %s",path_to_save)
            # Save the piece of file that is going to be parsed
            with open(path_to_save,'w') as fw:
                fw.writelines(log_lines)

        except Exception:
            raise DataSourceError(self,sys.exc_info()[0],method_name)
