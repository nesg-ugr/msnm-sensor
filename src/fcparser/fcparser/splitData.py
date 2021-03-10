#!/usr/bin/env python

import argparse
import glob
import sys
import re
import gzip
import os
import time
import yaml
from datetime import (datetime, timedelta)
from bisect import (bisect_left, bisect_right)


def main():
	init = time.time()
	args = getArguments()
	
	# Check input arguments
	try:
		parserConfig = getConfiguration(args.config)
	except IOError:
		print("No such config file '%s'" %(args.config))
		exit(1)
	except yaml.scanner.ScannerError as e:
		print("Incorrect config file '%s' (%s)" %(args.config, e.message))
		exit(1)
	try:
		timeWindow = timedelta(seconds=int(parserConfig['SPLIT']['Time']['window']))
		startTime  = parserConfig['SPLIT']['Time']['start']
		endTime    = parserConfig['SPLIT']['Time']['end']


	except KeyError as e:
		print("Missing config key (%s)" %(e.message))
		exit(1)
	except ValueError as e:
		print("Incorrect value (%s)" %(e.message))
		exit(1)
	if not isinstance(startTime, datetime):
		print("Incorrect time format: '%s'" %(startTime))
		exit(1)
	if not isinstance(endTime, datetime):
		print("Incorrect time format: '%s'" %(endTime))
		exit(1)
	
	data = {}
	SEPARATOR = {}

	for source in parserConfig['DataSources']:
		data[source] = {}
		print(source)
		
		try:
			config = getConfiguration(parserConfig['DataSources'][source]['config'])
			data[source]['input'] = parserConfig['DataSources'][source]['data']
			data[source]['output'] = str(parserConfig['SPLIT']['Output'])
			data[source]['tag'] = config['tag']
			data[source]['timestamp_format'] = config['timestamp_format']
			data[source]['struc'] = config['structured']
			
			if not data[source]['struc']:
				SEPARATOR[source] = config['separator']
				data[source]['timestamp_regexp'] = config['timestamp_regexp']
			
			else:
				data[source]['col'] = config['timearg']

		except KeyError as e:
			print("Missing config key in %s (%s)" %(source, e.message))
			exit(1)
		except ValueError as e:
			print("Incorrect value in %s (%s)" %(source, e.message))
			exit(1)
		try:
			data[source]['prefix'] = parserConfig['DataSources'][source]['prefix']
		except KeyError:
			data[source]['prefix'] = source
	

	print("-----------------------------------------------------------------------")
	print(" Start:  %s" %(startTime))
	print(" End:    %s" %(endTime))
	print(" Window: %s" %(timeWindow))
	print("-----------------------------------------------------------------------")

	
	# Create time bins
	if startTime and endTime:
		timeBins = [startTime]
		while timeBins[-1] < endTime:
			timeBins.append(timeBins[-1] + timeWindow)
	

	outputDir = data[source]['output']
	if not outputDir.endswith('/'):
		outputDir = outputDir + '/'
	if not os.path.exists(outputDir):
		#os.mkdir(outputDir)
		os.makedirs(outputDir)
		if args.verbose:
			print("** creating directory %s" %(outputDir))

	# Split data
	inputFiles = {}
	prefix = {}
	for source in data:
		print("SOURCE: %s" %(source))
	
		try:
			inputFiles[source] = glob.glob(data[source]['input'])
			
			# If the input data is in binary nfcapd, the data is preprocessed in the parsing process to obtain csv files.
			# so change input file pointer to new csv files.
			if 'nfcapd' in inputFiles[source][0]:
				new_input = "/".join(data[source]['input'].split('/')[:-1]) + '/netflow*' 
				inputFiles[source] = glob.glob(new_input)

			prefix[source] = data[source]['prefix']
		
		except:
			pass
		
	for source in inputFiles:
		if inputFiles[source] == []:
			data.pop(source)		

	print(startTime)
	current_year = startTime.year
	# Process of splitting 

	for source in data:

		print(source + ":")

		filecount = 0
		for path in inputFiles[source]:
			if path.endswith('.gz'):
		    		instream = gzip.open(path,'r')
			else:
				instream = open(path,'r')

			filecount += 1
			print("# %s/%s << %s" %(filecount, len(inputFiles[source]), os.path.split(path)[1]))

			if data[source]['struc']:
				linecount = 0
				openedStreams = {}
				order = []
				line = instream.readline()

				while line:
					if not line.startswith('#') and line.strip():
						t = getRecordTime(line, data[source]['col'], data[source]['timestamp_format'])
						pos = searchBin(timeBins, t)

						if pos is not None:
							if pos not in openedStreams:
								outputFile = outputDir + prefix[source] + timeBins[pos].strftime('-%Y%m%dt%H%M.csv')
								openedStreams[pos] = open(outputFile, 'a')
								order.append(pos)
								if args.verbose:
									print("   >> %s" %(os.path.split(outputFile)[1]))
								if len(openedStreams) > 500:
									old = order[0]
									openedStreams[old].close()
									del openedStreams[old]
									del order[0]

							openedStreams[pos].write(line)
							linecount += 1
					line = instream.readline()


				print("   Exported %d lines" %(linecount))
				print("   Elapsed: %s" %(prettyTime(time.time() - init)))

			else:

				logcount = 0
				openedStreams = {}
				order = []

				line = instream.readline()
				if line:
					log = ""

					while line:

						log += line 

						if len(log.split(SEPARATOR[source])) > 1:							
							logExtract = log.split(SEPARATOR[source])[0] 

							try:
								t = getUnstructuredTime(logExtract,data[source]['timestamp_regexp'],data[source]['timestamp_format'], current_year )
								pos = searchBin(timeBins,t)
							except:
								pos = None

							if pos is not None:
								if pos not in openedStreams:
									outputFile = outputDir + prefix[source] + timeBins[pos].strftime('-%Y%m%dt%H%M.csv')
									openedStreams[pos] = open(outputFile, 'a')
									order.append(pos)

									if args.verbose:
										print("   >> %s" %(os.path.split(outputFile)[1]))
									if len(openedStreams) > 500:
										old = order[0]
										openedStreams[old].close()
										del openedStreams[old]
										del order[0]

								openedStreams[pos].write(log)
								logcount += 1

							log = ""
							for n in log.split(SEPARATOR[source])[1::]:
								log += n

						line = instream.readline()

			    # Process last log:
				try:
					t = getUnstructuredTime(log,data[source]['timestamp_regexp'],data[source]['timestamp_format'], current_year)
					pos = searchBin(timeBins,t)

				except:
					pos = None

				if pos is not None:
					if pos not in openedStreams:
						outputFile = outputDir + prefix[source] + timeBins[pos].strftime('-%Y%m%dt%H%M.csv')
						openedStreams[pos] = open(outputFile, 'a')
						order.append(pos)

					openedStreams[pos].write(log)
					logcount += 1

				print("   Exported %d logs" %(logcount))
				print("   Elapsed: %s" %(prettyTime(time.time() - init)))

		for s in openedStreams:
			openedStreams[s].close()
			


def searchBin(bins, t):
	pos = bisect_right(bins, t) - 1
	return pos if t >= bins[0] and t<=bins[-1] else None

def getRecordTime(line, col, dateFormat):
	valueList = line.split(',')
	rawTime = valueList[col].split('.')[0]
	time = datetime.strptime(rawTime, dateFormat)
	return time

def getUnstructuredTime (log, patern, dateFormat, current_year):

	p = re.search(patern,log)
	date_string = p.group(0)

	d = datetime.strptime(date_string,dateFormat)
	if d.year == 1900:
	# 	d = d.replace(year = datetime.now().year)
		d = d.replace(year = current_year)

	return d

def prettyTime(elapsed):
	hours = int(elapsed // 3600)
	minutes = int(elapsed // 60 % 60)
	seconds = int(elapsed % 60)
	pretty = str(seconds) + " secs"
	if minutes or hours:
		pretty = str(minutes) + " mins, " + pretty
	if hours:
		pretty = str(hours) + " hours, " + pretty
	return pretty

def getConfiguration(config_file):
	stream = file(config_file, 'r')
	conf = yaml.load(stream)
	stream.close()
	return conf

def getArguments():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description='''Split data.''')
	parser.add_argument('config', metavar='CONFIG', help='Split Configuration File.')
	parser.add_argument('-v','--verbose', action='store_true', help='Show verbose information (files created)')
	args = parser.parse_args()
	return args


if __name__ == "__main__":
	main()
