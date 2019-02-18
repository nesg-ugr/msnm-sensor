# -*- coding: utf-8 -*-
"""
    :mod:`thread`
    ===========================================================================
    :synopsis: Common thread functions
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1
"""
import threading


class MSNMThread(threading.Thread, object):
        
    def __init__(self):
        threading.Thread.__init__(self)        
        self._stopped_event = threading.Event()
        self._stopped_event.is_set = self._stopped_event.isSet
    
    def run(self):
        # To be overridden
        pass
    
    def on_stop(self):
        # Should be overridden to do some stuff on thread stop
        pass
    
    def stop(self):
        self.on_stop()
        self._stopped_event.set()