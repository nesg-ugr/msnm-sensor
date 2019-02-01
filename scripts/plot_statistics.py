#!/home/roberto/anaconda2/bin/python2.7

'''
Created on 27 ene. 2017

@author: roberto
'''

import yaml
import logging.config
import sys, os
import numpy as np
import pandas as pd
import json

import matplotlib.pyplot as plt


def launch_show_output(staticFiles="./data/monitoring/output/",logscale=True, ucld=0.0, uclq=0.0):
    
    # Logging config
    logging.config.dictConfig(yaml.load(open('logging_static.yaml', 'r')))
    
    
    # Get all parsed *.dat files from a specific folder
    #staticFiles = "./data/monitoring/output/"
            
    # Get the name of the files ordered
    filesOrdered = np.sort(os.listdir(staticFiles))
            
    logging.debug("Got %s output files ",len(filesOrdered))
            
    # Remove auxiliar files weights.dat and stats.log
    filesOrdered = filesOrdered[np.logical_not('stats.log' == filesOrdered)]
    filesOrdered = filesOrdered[np.logical_not('weights.dat' == filesOrdered)]
            
    logging.debug("Removed unuseless files. Total files to process: %s ",len(filesOrdered))
            
    # Generate a dataframe containing all *.dat (all observations)
    # Date range as index
    #dstart = filesOrdered[0][7:][0:-4]# get initial timestamp from the first file name, e.g., output-20160209t1249.dat
    #dend = filesOrdered[-1][7:][0:-4]# get ending timestamp from the first file name, e.g., output-20160209t1249.dat
    #dstart = "201702071018"
    #dend = "201702071147"
    #d_range = pd.date_range(dstart,dend,freq='1min')
    dfAllObs = pd.DataFrame(filesOrdered,columns=['output'])
    
    # Get the test date range
#     date_range_start = local_dict[i]['staticObsRangeStart']
#     date_range_end = local_dict[i]['staticObsRangeEnd']
#     obsBySource[i] = dfAllObs[date_range_start:date_range_end]
            
    logging.debug("Got all output")
        
    # list of observations
    outputList = list(dfAllObs['output'])
    
    # q_values
    q_values = []
    #d_values 
    d_values = []
    
    
    for i in outputList:
        try:
            outputValues = np.loadtxt(staticFiles + i, comments="#", delimiter=",", skiprows=1)
            q_values.append(outputValues[0])
            d_values.append(outputValues[1])        
                        
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Exiting ...")
        except Exception:
            logging.warning("Probably we have reached the end of the observations. ERROR: %s", sys.exc_info()[1])
            
    
    
    q_range = np.arange(0,len(q_values))
    d_range = np.arange(0,len(d_values))    
    
    ax = plt.subplot(2, 1, 1)
    if logscale:
        ax.set_yscale("log", nonposy='clip')
    plt.axhline(y=float(uclq), xmin=np.min(q_range), xmax=np.max(q_range), color='red', linestyle='--')
    plt.bar(q_range, q_values)
    #plt.ylim(0,5)    
    #plt.title('Statistics')
    plt.xlabel(r'Obs')
    plt.ylabel(r'$Q_{1,1}$', fontsize=16)

    ax = plt.subplot(2, 1, 2)
    if logscale:
        ax.set_yscale("log", nonposy='clip')
    plt.axhline(y=float(ucld), xmin=np.min(d_range), xmax=np.max(d_range), color='red', linestyle='--')
    plt.bar(d_range, d_values)    
    plt.xlabel(r'Obs')
    plt.ylabel(r'$D_{1,1}$',fontsize=16)
    plt.bar(d_range, d_values)
    plt.savefig("monitoring.svg")  
    plt.savefig("monitoring.pdf")    
    plt.show()
    

if __name__ == '__main__':
    
    # Check the number of scripts params
    nparams = len(sys.argv)

    if nparams < 5:
        print("Use: plot_statistics.py <path_to_data> <logscale> <ucld> <uclq>")
        print("Example of use: plot_statistics.py ./config/scenario_4/results/20180102_162727/borderRouter/data/monitoring/output/ True 9.8 204.5")
        exit(1)
    
    launch_show_output(sys.argv[1],sys.argv[2], sys.argv[3], sys.argv[4])
    
