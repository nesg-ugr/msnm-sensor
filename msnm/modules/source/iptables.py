# -*- coding: utf-8 -*-
"""
    :mod:`IPTables data source implementation`
    ===========================================================================
    :synopsis: This module provides tools for getting and parsing iptables logs
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""

import re
from datetime import datetime
from dateutil import parser
from msnm.modules.config.configure import Configure
from msnm.exceptions.msnm_exception import DataSourceError
from msnm.modules.source.source import Source
import sys
import os
import logging
import shutil
from msnm.modules.thread.thread import MSNMThread
from msnm.utils import dateutils
import traceback

class IPTables(Source):
    """

    *IPTables*. It contains the basic methods to compute for getting, managing and parsing
    iptables logs information.

    See Also
    --------
    msnm.source.manager
    msnm.source
    """

    # Protocol constants
    TCP = "TCP"
    UDP = "UDP"

    # TCP flags
    # TODO perform as enumerate!
    URG_TCP_FLAG = "URG"
    ACK_TCP_FLAG = "ACK"
    PSH_TCP_FLAG = "PSH"
    RST_TCP_FLAG = "RST"
    SYN_TCP_FLAG = "SYN"
    FIN_TCP_FLAG = "FIN"

    def parse(self, file_to_parse, file_parsed, **kwargs):
        '''
        CSV parsing of a iptables log file portion as the input param ``file_to_parse``. The parsed CSV files is saved as the ``file_parsed`` param.
        The log is parsed following the nfdump format tool.

        Parameters
        ----------
        file_to_parse: str
            Path to iptables log file portion to parse
        file_parsed: str
            Path to the CSV output parsed file

        Raises
        ------
        DataSourceError

        '''

        method_name = "parse()"

        dateFormat = self.config.get_config()['GeneralParams']['dateFormat']
        # super(IPTables, self).parse(file_to_parse)

        TS_IP = re.compile(r"(\w+\s+\d+\s\d+:\d+:\d+).+SRC=([\d.]+)\s+DST=([\d.]+)")  # search for ts and IPs
        PORTS = re.compile("SPT=(.*?(?=\s))\s+DPT=(\d+)")  # search for ports
        PROTO = re.compile("PROTO=(.*?(?=\s))")  # search PROTO= string followed by any character and any number or repetitions until the first white space
        MAC = re.compile("MAC=(.*?(?=\s))")  # search MAC= string followed by any character and any number or repetitions until the first white space

        try:

            # contains all parsed csv lines
            parsed_lines = []

            # csv parsed file columns
            columns='DATE,SRC,DST,SMAC,DMAC,TMAC,SPT,DPT,PROTO,TCP_FLAGS,EVENT'

            # Note: with is in charge of to open and close the file
            with open(file_to_parse) as my_file:

                #df = pd.DataFrame(columns=columns, dtype=int)

                # Registered firewall events
                event_id = 1

                for line in my_file.xreadlines():

                    try:

                        # Search for IPs
                        ts_ip_port_match = TS_IP.search(line)

                        # Get timestamp
                        date = ts_ip_port_match.group(1)

                        # Format the date of the log
                        # date = datetime.strptime(date, '%b %d %H:%M:%S')
                        date = parser.parse(date)  # It manages all date format. Solves the issue found when using 'Aug  3 18:20:19'
                        date = date.replace(year=datetime.now().year)
                        date = date.strftime(dateFormat)

                        # Time stamp and Ips and ports
                        # Get the fields from *.log according to the groups in the regexp
                        src_addr = ts_ip_port_match.group(2)
                        dst_addr = ts_ip_port_match.group(3)

                        # Search for ports
                        ports_match = PORTS.search(line)
                        src_port = ports_match.group(1)
                        dst_port = ports_match.group(2)

                        # Search for MAC
                        mac_match = MAC.search(line)

                        # Check if MAC field exists
                        if mac_match:
                            # Get MAC
                            mac = mac_match.group(1)
                            dst_mac, src_mac, type_mac = self.get_params_from_mac(mac)
                        else:
                            dst_mac = ""
                            src_mac = ""
                            type_mac = ""

                        # Search for the protocol
                        protocol_match = PROTO.search(line)
                        protocol = protocol_match.group(1)

                        if protocol == self.TCP:
                            # Call super method format_tcp_flags()
                            tcp_flags = self.format_tcp_flags(self.get_tcp_flags(line), format_type='netflow')
                        else:
                            tcp_flags = ""

                    except AttributeError:
                        logging.warn("Attribute error: the iptables event cannot be parsed. Skipping line: %s",line)
                        continue

                    # Add new row to the dataframe
                    #df.loc[len(df)] = [date, src_addr, dst_addr, src_mac, dst_mac, type_mac, src_port, dst_port, protocol, tcp_flags, str(event_id)]

                    # Add new row to the list
                    parsed_lines.append(date + "," + src_addr + "," + dst_addr + "," + src_mac + "," + dst_mac + "," + type_mac + ","
                                        + src_port + "," + dst_port + "," + protocol + "," + tcp_flags + "," + str(event_id))
                    # Registered firewal events (one per line)
                    event_id = event_id + 1

            #df2 = df.set_index('DATE')

            # If there are optional parameters
            #TODO: activate if needed --> NOTE, this block works with DATAFRAMES!
#             if len(kwargs):
#                 # Get the corresponding lines of iptables.log from the first to the end timestamp in netflo file
#                 if 'netflow_dumps_path' in kwargs:
#                     # Get the synchronized lines
#                     df2 = self.get_synchronized_file_from_netflow_dump(df2, kwargs['netflow_dumps_path'])
#                 else:
#                     # Get the corresponding lines of iptables.log from a custom ts and sampling_rate minutes before.
#                     if 'ts_master_source' in kwargs:
#                         ts_master_source = kwargs['ts_master_source']
#                     else:
#                         # Current date by default
#                         ts_master_source = datetime.now().strftime(dateFormat)
#
#                     # Check the optional parameter sampling rate to get a temporal slice of lines of the log file
#                     if 'sampling_rate' in kwargs:
#                         sampling_rate = kwargs['sampling_rate']
#                     else:
#                         # 1 minute by default
#                         sampling_rate = 1
#                     # Get the synchronized lines
#                     df2 = self.get_synchronized_file(df2, ts_master_source, sampling_rate)

            # Save in csv as input of the PARSER
            #df2.to_csv(file_parsed, encoding='utf-8', header=False)

            # Save in csv as input of the PARSER
            with open(file_parsed,'w') as fl:
                fl.write(columns + "\n")
                fl.write("\n".join(parsed_lines))

        except DataSourceError as dse:
            raise dse
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback ,limit=5, file=sys.stdout)
            raise DataSourceError(self, sys.exc_info()[0], method_name)

        #return df2

    def start(self):
        #overriden from Source
        self._iptablesThread = IPTablesThread(self)
        self._iptablesThread.setName("IPTablesThread")
        self._iptablesThread.start()

    def stop(self):
        #overriden from Source
        self._iptablesThread.stop()

    def get_tcp_flags(self, line):

        """
        Searching for TCP flags from a log ``line``

        Parameters
        ----------
        line: src
            Log line

        Return
        ------
        found_flags_list: list
            A list including all found TCP flags. If a flag is not found it will be replaced by None


        Example
        -------
        >>> formatted_string = get_tcp_flags('Jan 17 09:02:48 roberto-PORTEGE-Z930 kernel: [40954.550702] IN= OUT=eth0 SRC=192.168.1.101 DST=52.214.217.91 LEN=114 TOS=0x00 PREC=0x00 TTL=64 ID=5117 DF PROTO=TCP SPT=56008 DPT=443 WINDOW=1444 RES=0x00 ACK PSH URGP=0')
        >>> print(formatted_string)
        >>> # it should returns [None, 'ACK', 'PSH', None, None, None]


        """

        end_ws = "(?=\s)"  # end with a white space only

        # Search por TCP flags
        urg_match = re.compile(self.URG_TCP_FLAG + end_ws).search(line)
        ack_match = re.compile(self.ACK_TCP_FLAG).search(line)
        psh_match = re.compile(self.PSH_TCP_FLAG).search(line)
        rst_match = re.compile(self.RST_TCP_FLAG).search(line)
        syn_match = re.compile(self.SYN_TCP_FLAG).search(line)
        fin_match = re.compile(self.FIN_TCP_FLAG).search(line)

        # list of flags
        found_flags_list = [None for i in range(6)]

        # Found?
        if urg_match:
            found_flags_list[0] = self.URG_TCP_FLAG
        if ack_match:
            found_flags_list[1] = self.ACK_TCP_FLAG
        if psh_match:
            found_flags_list[2] = self.PSH_TCP_FLAG
        if rst_match:
            found_flags_list[3] = self.RST_TCP_FLAG
        if syn_match:
            found_flags_list[4] = self.SYN_TCP_FLAG
        if fin_match:
            found_flags_list[5] = self.FIN_TCP_FLAG

        return found_flags_list

    def get_params_from_mac(self, complete_mac):

        """
        Getting different fields from the complete MAC address found in itpables log lines.

        # Complete MAC field from iptables log
        MAC=00:60:dd:45:67:ea:00:60:dd:45:4c:92:08:00

        # Different sub-fields from above
        00:60:dd:45:67:ea: Destination MAC=00:60:dd:45:67:ea
        00:60:dd:45:4c:92: Source MAC=00:60:dd:45:4c:92
        08:00 : Type=08:00 (ethernet frame carried an IPv4 datagram)

        Parameters
        ----------
        complete_mac: str
            MAC field found in a iptables log line

        Return
        ------
        dst_mac: str
            Destination MAC
        src_mac: str
            Source MAC
        type_mac: str
            MAC type

        Example
        -------
        >>> print get_params_from_mac('00:60:dd:45:67:ea:00:60:dd:45:4c:92:08:00')
        >>> #output
        >>> ('00:60:dd:45:67:ea', '00:60:dd:45:4c:92', '08:00')

        """

        dst_mac = complete_mac[0:17]
        src_mac = complete_mac[18:35]
        type_mac = complete_mac[36:]

        return dst_mac, src_mac, type_mac

class IPTablesThread(MSNMThread):
    """
    *IPTablesThread*. Iptables management thread. Among others actions, it is in charge of to get the log iptables lines according the observation interval time,
    parse them and call to the flow parser for built the iptables observation.

    Attributes
    ----------
    _iptables_instance: IPTables
        An IPTables instance

    See Also
    --------
    msnm.source.manager
    msnm.thread.thread
    msnm.source

    """

    def __init__(self, iptables_instance):
        super(IPTablesThread,self).__init__()
        self._iptables_instance = iptables_instance

    def run(self):

        method_name = "run()"

        iptables_log = self.config.get_config()['DataSources'][self._iptables_instance._type][self._iptables_instance.__class__.__name__]['captures']
        iptables_log_raw_folder = self.rootDataPath + self.config.get_config()['DataSources'][self._iptables_instance._type][self._iptables_instance.__class__.__name__]['raw']
        iptables_log_processed_folder = self.rootDataPath + self.config.get_config()['DataSources'][self._iptables_instance._type][self._iptables_instance.__class__.__name__]['processed']
        iptables_log_parsed_folder = self.rootDataPath + self.config.get_config()['DataSources'][self._iptables_instance._type][self._iptables_instance.__class__.__name__]['parsed']
        iptables_flow_parser_config_file = self.config.get_config()['DataSources'][self._iptables_instance._type][self._iptables_instance.__class__.__name__]['parserConfig']; # Parser configuration file for iptables
        timer = self.config.get_config()['GeneralParams']['dataSourcesScheduling']

        try:

            # Doing until stop request
            while not self._stopped_event.isSet():

                logging.info("Running iptables thread ...")

                logging.debug("Getting lines from file %s during %s seconds.",iptables_log, timer)
                # Get the iptables logs
                log_lines = self._iptables_instance.get_file_to_parse_time(iptables_log, timer)

                # Time stamp
                ts = dateutils.get_timestamp()

                # Path for the backup
                iptables_raw_log_file = iptables_log_raw_folder + "iptables_" + ts + ".log"
                self._iptables_instance.save_file(log_lines, iptables_raw_log_file)

                # Parse it in *.csv format
                logging.debug("Parsing file %s",iptables_raw_log_file)
                iptables_log_processed_file = iptables_log_processed_folder + "iptables_" + ts + ".csv"
                self._iptables_instance.parse(iptables_raw_log_file, iptables_log_processed_file)

                # Copy CSV file to parsed folder to be parsed by the flow parsed
                iptables_log_parsed_file = iptables_log_parsed_folder + "iptables_" + ts + ".csv"
                logging.debug("Copying file %s to %s ",iptables_log_processed_file, iptables_log_parsed_file)
                shutil.copyfile(iptables_log_processed_file, iptables_log_parsed_file)

                # Flow parser
                logging.debug("Running flow parser for %s file config.",iptables_flow_parser_config_file)
                self._iptables_instance.launch_flow_parser(iptables_flow_parser_config_file)

                # Add the *.dat output from parser to the dict of generated files
                self._iptables_instance._files_generated[ts] = iptables_log_parsed_folder + "output-iptables_" + ts + ".dat"

                # Remove CSV file once it is parsed successfully
                logging.debug("Deleting file %s",iptables_log_parsed_file)
                os.remove(iptables_log_parsed_file)


        except DataSourceError as edse:
            logging.error("Error processing iptables source: %s",edse.get_msg())
            raise edse
        except IOError as ioe:
            logging.error("Error processing iptables source: %s",ioe.get_msg())
            raise DataSourceError(self, sys.exc_info()[0], method_name)
