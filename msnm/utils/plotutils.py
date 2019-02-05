# -*- coding: utf-8 -*-
"""
    :mod:`Plot tools and utilities`
    ===========================================================================
    :synopsis: Tools for plotting
    :author: NESG (Network Engineering & Security Group) - https://nesg.ugr.es
    :contact: nesg@ugr.es, rmagan@ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 0.0.1  
"""

import matplotlib.pyplot as plt
#plt.style.use('ggplot')
#plt.ion()

class DynamicUpdate():
    '''
    Contains methods to initialize a bar plot and to dynamically update it through new date
    
    '''
   
    def on_launch(self,min_x,max_x):
        '''
        Initialize the bar plot
        
        '''
        #Set up plot
        self.figure, self.ax = plt.subplots()
        self.lines = self.ax.bar([],[])                        
        
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True)
        self.ax.set_xlim(min_x, max_x)
        #Other stuff
        self.ax.grid()

    def on_running(self, xdata, ydata, labels):
        '''
        New data to be plotted
        '''
        plt.cla()
        #Update data (with the new _and_ the old points)
        #self.lines.set_xdata(xdata)
        #self.lines.set_ydata(ydata)
        self.ax.bar(xdata,ydata)
        plt.xticks(xdata,labels,rotation='vertical')
        plt.tick_params(axis='both', which='major', labelsize=10)
        plt.tick_params(axis='both', which='minor', labelsize=8)
        #Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        #We need to draw *and* flush
        self.figure.canvas.draw()        
        self.figure.canvas.flush_events()            

    #Example
    def __call__(self):
        import numpy as np
        import time
        self.on_launch(0,10)
        xdata = []
        ydata = []
        for x in np.arange(0,10,0.5):
            xdata.append(x)
            ydata.append(np.exp(-x**2)+10*np.exp(-(x-7)**2))
            self.on_running(xdata, ydata,[])
            time.sleep(1)
        return xdata, ydata


dynUpdate = DynamicUpdate()
# Example of a dynamic visualization
dynUpdate.__call__()
    
