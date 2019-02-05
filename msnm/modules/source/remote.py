'''
Created on 19 sept. 2016

@author: roberto
'''
from msnm.modules.source.source import Source

class RemoteSource(Source):
    
    def __init__(self):
        super(RemoteSource, self).__init__()
        self._type = Source.TYPE_R