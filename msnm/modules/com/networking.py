# -*- coding: utf-8 -*-
"""
    :mod:`Communications module`
    ===============================================================================
    :synopsis: It is in charge of providing the communication support among sensors
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

import logging
import socket
import SocketServer
import pickle
from msnm.modules.thread.thread import MSNMThread
import traceback
import sys
from msnm.modules.com.packet import Packet, DataPacket, ResponsePacket
from msnm.modules.config.configure import Configure
from msnm.utils import dateutils
from msnm.utils import datautils
import numpy as np
from msnm.exceptions.msnm_exception import CommError, MSNMError
import threading
from msnm.modules.source.source import Source

class TCPServerThread(MSNMThread):
    
    """
        
    *Thread wrapper to manage the TCP server functional states*
        
    Attributes
    ----------
    _server: 
        instance of the server which manages a specific client request
         
    See Also
    --------
    MSNMThread
    Packet
    """ 
    
    def __init__(self, server):
        super(TCPServerThread,self).__init__()
        self._server = server
    
    def run(self):
        logging.info("Running the TCP server")
        self._server.serve_forever()
        
    def on_stop(self):
        logging.info("Shutdown the TCP server ...")
        self._server.shutdown()
        

class MSNMTCPServerRequestHandler(SocketServer.BaseRequestHandler):
    
    """
        
    *Client requests handler*
        
    """ 

    def handle(self):
        # Echo the back to the client
        data = self.request.recv(1024).strip()
                                        
        # Data received management        
        self.server.manage_data(data,self.client_address)
        
        # Send response                                
        self.server.send_response(self.request, Packet.OK)
        
        return

class MSNMTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    
    """
        *TCP concurrent server*
            
        Attributes
        ----------
        _remotes: dict 
            dictionary containing all the valid remote sources previously configured
        _packet_sent: int
            countering the total number of packet sent by this server. This includes the response
            packets sent to the client
        _packet_recv: int
            countering the total number of packet received.
             
        See Also
        --------
        MSNMTCPServerRequestHandler
        SocketServer.ThreadingMixIn
        SocketServer.TCPServer
        Packet
    """ 
    
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        # Remote sources
        self._remotes = {}
        # number of packets sent. They can be of response and data types.            
        self._packet_sent = 0
        # number of packets received.
        self._packet_recv = 0

    def handle_error(self, request, client_address):
        SocketServer.TCPServer.handle_error(self, request, client_address)
        self.send_response(request, Packet.KO)
            
    def manage_data(self, data, client_address):
    
        """
        Depending on the type of the received package this method selects the corresponding procedure to process it.
            
        Parameters
        ----------
        data: str
            the received serialized data
        client_address: 
            client address
    
        """
        
        # Reception timestamp
        ts_rec = dateutils.get_timestamp()
        
        # Client IP
        client_IP = client_address[0]
        
        # De-serialized the received data
        pack = pickle.loads(data)
        
        logging.info("Data received from sensor: %s (%s) at %s. Package type: %s",pack._header['sid'],client_IP,ts_rec, pack._type)
        
        # Data packet
        if pack._type == Packet.TYPE_D:         
            # Save the packet
            self.save_packet(pack,client_address,ts_rec)
        
        # Command packet
        elif pack._type == Packet.TYPE_C:
            # TODO fill additional package fields
            # Do diagnosis
            pass
        else:
            # Error
            logging.warn("The received packet is not a valid type. Type: %s", pack._type)
                
        return pack
    
    def save_packet(self,pack, client_addres,ts_rec):
        
        """
        Save the packet to the file system
            
        Parameters
        ----------
        pack: Packet
            the packet received
        client_address: 
            client address
        ts_rec: str
            packet reception ts
            
        Raise
        -----
        CommError
    
        """
    
        # Source sensor ID
        sid = pack._header['sid']
        
        try:
        
            # check is the source exists
            if self._remotes.has_key(sid):
            
                logging.info("Saving packet from sensor %s (%s)", sid,client_addres[0])
                
                config = Configure()    
                valuesFormat = config.get_config()['GeneralParams']['valuesFormat'] # how the variables of the complete observation are saved
                # to save the complete remote packet received in JSON
                raw_remote_source_path = config.get_config()['DataSources'][Source.TYPE_R][sid]['raw']
                raw_remote_source_file = raw_remote_source_path + sid + "_" + ts_rec + ".json"
                
                # Convert the packet to json format
                p_json = datautils.pack2json(pack)            
                
                # Save raw data
                with open(raw_remote_source_file,'w') as f:        
                    f.write("# from: " + client_addres[0] + "\n")
                    f.writelines(p_json)  
                    
                logging.debug("\n%s",p_json)      
                
                # to save the body of the packet --> Just for data packet
                parsed_remote_source_path = config.get_config()['DataSources'][Source.TYPE_R][sid]['parsed']
                parsed_remote_source_file = parsed_remote_source_path + "output-" + sid + "_" + ts_rec + ".dat"
                
                # Save parsed data. The content of packet body
                statistics_values = np.array([i for i in pack._body.values()])
                name_statistics = [i for i in pack._body.keys()]
                # 1xM array
                statistics_values = statistics_values.reshape((1,statistics_values.size))
                np.savetxt(parsed_remote_source_file, statistics_values, valuesFormat, delimiter=",", header=str(name_statistics), comments="#")
                
                # Add the *.dat output from parser to the dict of generated files
                # The key is the packet reception time stamp not the ts of received as packet field.
                self._remotes[sid]._files_generated[ts_rec] = parsed_remote_source_file
                
                logging.info("Ending saving packet from sensor %s (%s)", sid,client_addres[0])
            else:
                logging.warn("The data source %s is not a known remote data source or it has not been configured correctly.",sid)
                logging.warn("The received packet will not be processed :(")
        except IOError as ioe: 
            logging.error("Error opening writing in file %s : %s",raw_remote_source_file,sys.exc_info()[1])
            raise CommError(ioe, sys.exc_info()[1], "save_packet()")
        except Exception as e:
            logging.error("Error when saving packet received with ID=%s : %s",sid,sys.exc_info()[1])            
            raise CommError(e, sys.exc_info()[1], "save_packet()")
                                
    def send_response(self,request,msg):
        
        """
        Sending the response to the client
        
        Parameters
        ----------
        request:
            client request
        msg: str
            response msg
            
        """
        
        # Sensor ID. The current sensor ID that sends the response
        config = Configure()
        sid = config.get_config()['Sensor']['sid']
                
        # sent timestamp
        ts = dateutils.get_timestamp()
                
        # build a response message           
        pack_resp = ResponsePacket()
        pack_resp.fill_header({'id':self._packet_sent,'sid':sid,'ts':ts,'type':Packet.TYPE_R})
        pack_resp.fill_body({'resp':msg})
            
        # Response packet
        p_serialized = pickle.dumps(pack_resp, 2)
        request.send(p_serialized)
                
        # increment the number of packets sent
        self._packet_sent =  self._packet_sent + 1         
        
    def set_remotes(self,remotes):
        self._remotes = remotes                                

class TCPClientThread(MSNMThread):
    
    """
        *TCP client thread*
            
        Attributes
        ----------
        _clint_instance: TCPClient
            client communication manager
             
        See Also
        --------
        MSNMTCPServerRequestHandler
        SocketServer.ThreadingMixIn
        SocketServer.TCPServer
        Packet
    """ 
    
    def __init__(self, client):
        super(TCPClientThread, self).__init__()
        self._client_instance = client
        
    def run(self):
        
        method_name = "run()"
        
        logging.info("Running client thread. Thread: %s", threading.current_thread().getName())
        
        try:            
            
            # Send pack to the server
            client_sock = self._client_instance.send_msg_to_server(self._client_instance._packet)
                        
            logging.debug("Sending packet to %s", self._client_instance._server_address)
            
            # Get response from server
            response = self._client_instance.recv_msg_from_server(client_sock)
            
            logging.debug("Server %s sent the response %s",self._client_instance._server_address, response._body['resp'])
        except CommError as ce:
            logging.error(ce.get_msg())
            #TODO: do some method to manage the raised exception in child threads on the main thread            
            raise MSNMError(self, ce.get_msg(), method_name)
                            
class TCPClient(object):
    
    """
        *TCP client*
        
        Attributes
        ----------
        _packet_sent: int
            number of packet sent
             
        See Also
        --------
        TCPClientThread
        
    """ 
    
    _lock = threading.Lock()
        
    def __init__(self):
        self._packet_sent = 0

    def send_msg_to_server(self, pack):
        
        """
        Sending packet to the server
        
        Parameters
        ----------
        packet: Packet
            The packet to send
        
        Return
        ------
        client: socket
            client socket
            
        Raise
        -----
        CommError
        
        """
        
        method_name = "send_msg_to_server()"
        
        # load config
        config = Configure()
        conn_timeout = config.get_config()['GeneralParams']['serverConnectionTimeout']
        
        logging.info("Sending packet %s to server %s",pack._header['id'], self._server_address)
                
        # Serialize the packet
        p_serialized = pickle.dumps(pack, 2)
        
        # IP and port of the server
        ip, port = self._server_address 
                
        try:
            # Connect to the server
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(conn_timeout)            
            client.connect((ip, port))
            logging.debug("Connected to server %s",self._server_address)        
        except socket.error as se:
            logging.error("Error creating a new connection to %s",self._server_address)
            client.close()
            raise CommError(se,sys.exc_info()[1],method_name)
            
        # Send msg
        client.send(p_serialized)
        
        logging.info("Packet %s has been sent to server %s",pack._header['id'], self._server_address)
        
        return client      
    
    def recv_msg_from_server(self,client):
        
        """
        Receiving response from server
        
        Parameters
        ----------
        client:
            client socket
        
        Return
        ------
        p_response: Packet
            The response packet
            
        Raise
        -----
        CommError
        
        """
        
        method_name = "recv_msg_from_server()"
        
        logging.info("Receiving packet from server ...")
        
        try:
            response = client.recv(1024)
        except socket.error as se:
            logging.error("Error receiving message from server %s",self._server_address)
            client.close()
            raise CommError(se,sys.exc_info()[1],method_name)
        
        # De-serializing the packet
        p_response = pickle.loads(response)
        
        logging.info("Packet %s received",p_response._header['id'])
        
        return p_response
    
    def set_packet_to_send(self, packet):
        self._packet = packet
    
    def set_server_address(self, server_address):
        with self._lock:       
            self._server_address = server_address

    
    