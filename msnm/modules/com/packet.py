# -*- coding: utf-8 -*-
"""
    :mod:`packet`
    ===========================================================================
    :synopsis: It describes all fo the available packets used by the sensor
    :author: NESG (Network Engineering & Security Group)
    :contact: rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""
class Packet(object):
    
    # Flags received to discern among types of packages
    TYPE_D = "D" # Data normal packets e.g., monitoring packet containing Q and T statistics
    TYPE_C = "C" # Command packets to start whatever the operation e.g., to change the mode of the sensor from monitoring to calibration
    TYPE_R = "R" # Response packets towards the client
    TYPE_EMPTY = "" # Empty packet. TODO: define what is exactly an empty packet
    
    # Types of response body for response packets
    OK = "OK"
    KO = "KO"

    def __init__(self, packet_type):
        self._type = packet_type
        self._header = {}
        self._body = {}
    
    def fill_header(self, header={}):
        # to be overridden
        pass
    
    def fill_body(self, body={}):
        # to be overridden
        pass

class DataPacket(Packet):
    
    def __init__(self):
        super(DataPacket, self).__init__(Packet.TYPE_D)
        
    def fill_header(self, header={}):
        self._header = header
        
    def fill_body(self, body={}):
        self._body = body
        
class CommandPacket(Packet):
    
    def __init__(self):
        super(CommandPacket, self).__init__(Packet.TYPE_C)
        
    def fill_header(self, header={}):
        self._header = header
        
    def fill_body(self, body={}):
        self._body = body
        
class ResponsePacket(Packet):
    
    def __init__(self):
        super(ResponsePacket, self).__init__(Packet.TYPE_R)
        
    def fill_header(self, header={}):
        self._header = header
        
    def fill_body(self, body={}):
        self._body = body
        
    
    
    
    
        
