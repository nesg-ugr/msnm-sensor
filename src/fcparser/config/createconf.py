#!/usr/bin/env python

"""
createconf -- Builds a FCParser config file for a data source out of a json with counts. This is usefull to automatically decide the features of the system.

Authors: Jose Camacho (josecamacho@ugr.es)
	 
Last Modification: 7/Jul/2018

"""

import argparse
import os
import yaml
import json


def main(call='external',jsonfile='',yamlfile='',structured='True',tformat='%m/%d-%H:%M:%S',tregexp='[0-9]{1,2}/[0-9]{1,2}-([0-9]{1,2}:){2}[0-9]{2}',sep='"\n\n"',targ=1):
	
	# if called from terminal
	# if not, the parser must be called in this way: createconf.main(call='internal',jsonfile='<route_to_json_file>',yamlfile='<name_output_file>',structured='<True for structured source>, tformat='<timestamp format>',tregexp='<regular expression for timestamp>',separator='<separator between logs>',targ='<time argument in structured sources')
	if call is 'external':
		args = getArguments()
		jsonfile = args.json
		yamlfile = args.yaml
		tformat = args.tformat
		tregexp = args.tregexp
		separator = args.separator
		targ = args.targ
		structured = args.s
	
	# read json 
	try:
    		with open(jsonfile, 'r') as f:
			datastore = json.load(f)
	except:
    		print("File " + jsonfile +  " could not be open.")
    		quit()

	# select the features according to the counts
	datastore = filterFeatures(datastore) 
		
	# prepare yaml data

	header = '''#-----------------------------------------------------------------------
#
# Datasource- Configuration File generated with createconf
#
#-----------------------------------------------------------------------
'''

	content = dict()
	content['tag'] = 'autocreated'
	content['structured'] = structured
	content['timestamp_format'] = tformat
 
	if structured:
		content['timearg'] = targ
	else:
		content['timestamp_regexp'] =  tregexp
		content['separator'] = separator


	contentv = dict()
	contentv['VARIABLES'] = list()

	for varis in datastore:
		interm = dict();
		interm['name'] = str(varis)
		interm['matchtype'] = 'string'
		#interm['where'] =  "\'" + str(varis) + "\'"
		#contentv['VARIABLES'].append(interm)
		#interm['name'] = varis
		#interm['matchtype'] = 'string'
		interm['where'] =  str(varis)
		contentv['VARIABLES'].append(interm)


	contentf = dict()
	contentf['FEATURES'] = list()

	for varis in datastore:
		interm = dict();
		interm['name'] = str(varis)
		interm['variable'] = str(varis)
		interm['matchtype'] = 'regexp'
		#interm['value'] = "\'" + str(varis) + "\'"
		#contentf['FEATURES'].append(interm)
		#interm['name'] = varis
		#interm['variable'] = varis
		#interm['matchtype'] = 'regexp'
		interm['value'] = str(varis)
		contentf['FEATURES'].append(interm)


	# write resuls in yaml
	try:
		stream = file(yamlfile, 'w')
		
		stream .write(header)
		stream .write('\n\n')
		yaml.dump(content, stream, default_flow_style=False)
		stream .write('\n\n')
		yaml.dump(contentv, stream, default_flow_style=False)
		stream .write('\n\n')
		yaml.dump(contentf, stream, default_flow_style=False)
	except:
    		print("Problem writing " + yamlfile)
    		quit()

	


    	
def getArguments():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description='''This program builds a FCParser config file for a data source out of a json with counts.''')
	parser.add_argument('json', metavar='jsonfile', help='The json file with counts.')
	parser.add_argument('yaml', metavar='yamlfile', help='The name for the output yaml configuration file.')
	parser.add_argument('-tf', dest='tformat', metavar='tformat', help='Timestamp format.', default='%m/%d-%H:%M:%S')
	parser.add_argument('-tr', dest='tregexp', metavar='tregexp', help='Regular expression for timestamp.', default='[0-9]{1,2}/[0-9]{1,2}-([0-9]{1,2}:){2}[0-9]{2}')
	parser.add_argument('-se', dest='separator', metavar='separator', help='Separator between logs.', default="\"\\n\\n\"")
	parser.add_argument('-ta', dest='targ', metavar='targ', help='Time argument in structured sources.', default=1)
	parser.add_argument('-s', action='store_true', help='Structured source.')
	return parser.parse_args()

def filterFeatures(datastore):
	return datastore
#datastore['total']

if __name__ == "__main__":
	
	main()
