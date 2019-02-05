'''
Created on 9 sept. 2016

@author: roberto
'''
import threading
# import time
# import numpy as np

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
        
#         timetowait = np.random.randint(10)
#         print "Thread %s is waiting %d seconds.\n" %(threading.current_thread().getName(),timetowait)
#         time.sleep(timetowait)
        
 
# if __name__ == '__main__': 
#     
#     for i in range(5):
#         t = IPTablesThread()
#         t.start()
#         
#     print "# of threads: %s" %(len(threading.enumerate()))
#     for i in threading.enumerate():
#         print "Thread %s" %(i.getName())
#         
#     for i in threading.enumerate():
#         if i is not threading.currentThread():
#             i.join()
#         
#     print "Finish .."
        
    
        
        