#!/usr/bin/env python

"""
parser -- Program for parsing and processing raw network
data and preparing it for further multivariate analysis using
FaaC parser library.


Authors: Alejandro Perez Villegas (alextoni@gmail.com)
		 Jose Manuel Garcia Gimenez (jgarciag@ugr.es)
		 
Last Modification: 21/Sep/2017

"""

import argparse
import glob
import os
import re
import time
import gzip
import shutil
import yaml
import subprocess

from . import faaclib

def main(call='external',configfile=''):
	
	startTime = time.time()
	# if called from terminal
	# if not, the parser must be called in this way: fcparser.main(call='internal',configfile='<route_to_config_file>')
	if call is 'external':
		args = getArguments()
		configfile = args.config
		

	delete_nfcsv = None # variable for netflow raw data  	

	try:
		parserConfig = getConfiguration(configfile)
	except IOError:
		print(("No such config file '%s'" %(configfile)))
		exit(1)
	except yaml.scanner.ScannerError as e:
		print(("Incorrect config file '%s'" %(configfile)))
		print((e.problem))
		print((e.problem_mark))
		exit(1)
	try:
		dataSources = parserConfig['DataSources']
		output = parserConfig['Output']
	except KeyError as e:
		print(("Missing config key: %s" %(e.message)))
		exit(1)


	# Output settings
	try:
		OUTDIR = output['dir']
		if not OUTDIR.endswith('/'):
			OUTDIR = OUTDIR + '/'
	except (KeyError, TypeError):
		OUTDIR = 'OUTPUT/'
		print((" ** Default output directory: '%s'" %(OUTDIR)))
	try:
		OUTSTATS = output['stats']
	except (KeyError, TypeError):
		OUTSTATS = 'stats.log'
		print((" ** Default log file: '%s'" %(OUTSTATS)))
	try:
		OUTW = output['weights']
	except (KeyError, TypeError):
		OUTW = 'weights.dat'
		# print " ** Default weights file: '%s'" %(OUTW)
		
	# Sources settings	
	SOURCES = {}
	for source in dataSources:
		SOURCES[source] = {}
		try:
			SOURCES[source]['CONFIG'] = getConfiguration(dataSources[source]['config'])
			SOURCES[source]['FILES'] = glob.glob(dataSources[source]['data'])
		except KeyError as e:
			print(("Missing key '%s' in datasource '%s'." %(e.message, source)))
			exit(1)
		except IOError:
			print(("No such config file '%s'" %(dataSources[source]['config'])))
			exit(1)
		except yaml.scanner.ScannerError as e:
			print(("Incorrect config file '%s'" %(dataSources[source]['config'])))
			print((e.problem))
			print((e.problem_mark))
			exit(1)
	try:
		Keys = parserConfig['Keys']
	except KeyError as e:
		Keys = None 

	FEATURES = {}
	STRUCTURED = {}
	SEPARATOR = {}

	try:
		for source in SOURCES:
			FEATURES[source] = SOURCES[source]['CONFIG']['FEATURES']
			STRUCTURED[source] = SOURCES[source]['CONFIG']['structured']
			
			if not STRUCTURED[source]:
				SEPARATOR[source] = SOURCES[source]['CONFIG']['separator']	

	except KeyError as e:
		print(("Missing config key: %s" %(e.message)))
		exit(1)

	# Preprocessing nfcapd files to obtain csv files.
	for source in dataSources:
		out_files = []
		for file in SOURCES[source]['FILES']:
			if 'nfcapd' in file:

				out_file = '/'.join(file.split('/')[:-1]) + '/temp_' + file.split('.')[-1] + ""
				os.system("nfdump -r " + file + " -o csv >>"+out_file)
				os.system('tail -n +2 '+out_file + '>>' + out_file.replace('temp',source))
				os.system('head -n -3 ' + out_file.replace('temp',source) + ' >> ' + out_file.replace('temp',source) + '.csv')
				out_files.append(out_file.replace('temp',source) + '.csv')
				os.remove(out_file)
				os.remove(out_file.replace('temp',source))
		
				SOURCES[source]['FILES'] = out_files
				delete_nfcsv = out_files




	# If there are split parameters, perform split procedure
	if not (parserConfig['SPLIT']['Time']['window'] == None or parserConfig['SPLIT']['Time']['start'] == None or parserConfig['SPLIT']['Time']['end'] == None):
		
		print("\n\nSPLITTING DATA\n\n")
		retcode = subprocess.call("python "+ os.path.dirname(__file__) +"/splitData.py "+ configfile, shell=True)

		if retcode == 0:
			pass  # No exception, all is good!
		else:
			print("Error splitting data")
			exit(1)
		
		for source in dataSources:
		 	SOURCES[source]['FILES'] = glob.glob(str(parserConfig['SPLIT']['Output']) + source + "*" )

	else:
		print("\n\n**WARNING**: No split configuration, or split missconfiguration\n\n")



	# Print a summary of loaded parameters
	print("-----------------------------------------------------------------------")
	print("Data Sources:")
	for source in SOURCES:
		print((" * %s %s variables   %s features" %((source).ljust(18), str(len(SOURCES[source]['CONFIG']['VARIABLES'])).ljust(2), str(len(SOURCES[source]['CONFIG']['FEATURES'])).ljust(3))))
	print((" TOTAL %s features" %(str(sum(len(l) for l in list(FEATURES.values()))))))
	print()
	print("Key:") 	
	aggrStr = ', '.join(Keys) if isinstance(Keys,list) else Keys
	print(aggrStr)
	print()
	print("Output:")
	print(("  Directory: %s" %(OUTDIR)))
	print(("  Stats file: %s" %(OUTSTATS)))
	print(("  Weights file: %s" %(OUTW)))
	print("-----------------------------------------------------------------------\n")
	

	# Create output directory
	if not os.path.exists(OUTDIR):
		os.mkdir(OUTDIR)
		print(("** creating directory %s" %(OUTDIR)))


	# Create log files
	statsPath = OUTDIR + OUTSTATS
	statsStream = open(statsPath, 'w')

	statsStream.write("STATS\n")
	statsStream.write("=================================================\n\n")
	stats = {}



	features = []
	weigthts = []

	for source in FEATURES:
		# Create weight file

		for feat in SOURCES[source]['CONFIG']['FEATURES']:
			try:	
				features.append(feat['name'])
			except:
				print(("FEATURES: missing config key (%s)" %(e.message)))
				print((FEATURES[source][i]))
				exit(1)				
			try:
				weigthts.append(str(feat['weight']))
			except:
				weigthts.append('1')

	weightsPath = OUTDIR + OUTW
	weightsStream = open(weightsPath, 'w')
	weightsStream.write(', '.join(features) + '\n')
	weightsStream.write(', '.join(weigthts) + '\n')
	weightsStream.close()

	# Count lines of datasources, for stats purposes.
	lines = {}
	for source in SOURCES:
		lines[source] = 0
		
		for file in SOURCES[source]['FILES']:
			if STRUCTURED[source]:
				lines[source] += file_len(file)

			else:
				lines[source] += file_log_len(file,SEPARATOR[source])
	
	# Sum lines from all datasources to obtain tota lines.
	total_lines = 0

	stats['lines'] = {}
	for source in lines:
		total_lines += lines[source]
		stats['lines'][source] = lines[source]

	# Get a dictionary with all de var names 
	# to check if sources are unused due to choosen key
	if Keys:
		var_names = {}
		for source in SOURCES:
			var_names[source] = []
			for variable in  range(len(SOURCES[source]['CONFIG']['VARIABLES'])):
				var_names[source].append(SOURCES[source]['CONFIG']['VARIABLES'][variable]['name'])

	# Count in witch source the key does not appear
		unused_sources=[]
		for source in var_names:
			if isinstance(Keys,list):
				if not all(x in var_names[source] for x in Keys):
					SOURCES.pop(source, None)
					unused_sources.append(source)
			else:
				if Keys not in var_names[source]:
					SOURCES.pop(source, None)
					unused_sources.append(source)

	# Count unused lines from all unused sources
	# in order to calculate a percentage of used entries.
		unused_lines = 0 
		for source in unused_sources:
			if source in list(lines.keys()):				
				unused_lines += lines[source]



		if unused_sources:
			print("\n\n###################################################################################################")
			print("                                                                                                       ")
			print("                   WARNING: DATASOURCES UNUSED DUE TO CHOOSEN KEY                                      ")
			print(("                   UNUSED DATASOURCES:     " +str(unused_sources) +"                                   "))
			print(("                   PERCENTAGE OF USED ENRIES: " +str(float(total_lines - unused_lines)*100/total_lines))) 
			print("                                                                                                       ")
			print("###################################################################################################\n\n")
			

			statsLine = "#------------------------------------------------\n"
			statsStream.write(statsLine)
			statsLine = "WARNING: DATASOURCES UNUSED DUE TO CHOOSEN KEY\n"
			statsStream.write(statsLine)
			statsLine = "UNUSED DATASOURCES:     " +str(unused_sources) +"\n"
			statsStream.write(statsLine)
			statsLine = "PERCENTAGE USED ENRIES: " +str(float(total_lines - unused_lines)*100/total_lines) +"\n"
			statsStream.write(statsLine)
			statsLine = "#------------------------------------------------\n\n"
			statsStream.write(statsLine)

	
	# Extracting stats info, used and unused lines:

	stats['unused_lines'] = {}

	for source in SOURCES:
		stats['unused_lines'][source] = 0

	if Keys:
		if unused_sources:
			for unused_source in unused_sources:
				stats['unused_lines'][unused_source] = lines[unused_source]

	# Process files
	# ==============

	OBSERVATIONS = {}
	count_total = 0

	# Iterate through datasources.
	for source in SOURCES:
		count = 0
		OBSERVATIONS[source] = {}

		currentTime = time.time()

		print("\n-----------------------------------------------------------------------\n")
		print(("Elapsed: %s \n" %(prettyTime(currentTime - startTime))))	

		# Iterate through files.


		for i in range(len(SOURCES[source]['FILES'])):
			input_path = SOURCES[source]['FILES'][i]
			if input_path:
				
				count += 1
				count_total += 1
				tag = getTag(input_path)

				# Print some progress stats
				print(("%s  #%s / %s  %s" %(source, str(count), str(len(SOURCES[source]['FILES'])), tag)))	
				
				# Loop for structured sources
				if STRUCTURED[source]:

					# Start reading the file		
					if input_path.endswith('.gz'):
		    				input_file = gzip.open(input_path,'r')
					else:
						input_file = open(input_path,'r')

					line = input_file.readline()


					# Create observation batch
					try:
						obsBatch = faaclib.ObservationBatch()
					except faaclib.ConfigError as e:
						print((e.msg))
						exit(1)

					while line:
						#Extract one record from each line of the file
						record = faaclib.Record(line,SOURCES[source]['CONFIG']['VARIABLES'], STRUCTURED[source])
				
						# Generate and aggregate observation
						obs = faaclib.AggregatedObservation(record, FEATURES[source], Keys)
						obsBatch.add(obs)
						line = input_file.readline()

				# Loop for unstructured sources
				else:

					# Start reading the file
					if input_path.endswith('.gz'):
		    				input_file = gzip.open(input_path,'r')
					else:
						input_file = open(input_path,'r')

					line = input_file.readline()


					if line:
						# Create observation batch
						try:
							obsBatch = faaclib.ObservationBatch()
						except faaclib.ConfigError as e:
							print((e.msg))
							exit(1)

						# Now, reading logs instead of lines, read until separator		
						log ="" + line

						while line:

							# Add lines to log until separator is reached.
							log += line 

							if len(log.split(SEPARATOR[source])) > 1:

								# for each log generate one record and convert into observation
								logExtract = log.split(SEPARATOR[source])[0]
								record = faaclib.Record(logExtract,SOURCES[source]['CONFIG']['VARIABLES'], STRUCTURED[source])
								aggregate_bool = True
								
								if Keys:
									if not isinstance(Keys,list):
										Keys = [Keys]
									for key in Keys:
										if (record.variables[key] == None): 
											aggregate_bool = False

								if aggregate_bool:

									# Generate and aggregate observation
									obs = faaclib.AggregatedObservation(record, FEATURES[source], Keys)
									obsBatch.add(obs)


								log = ""
								for n in logExtract.split(SEPARATOR[source])[1::]:
									log += n

							line = input_file.readline()

						
						# Add the last log after the last separator.
						log += line
						record = faaclib.Record(log,SOURCES[source]['CONFIG']['VARIABLES'], STRUCTURED[source])
						
						aggregate_bool = True

						if Keys:
							if not isinstance(Keys,list):
								Keys = [Keys]
							for key in Keys:
								if (record.variables[key] == None): 
									aggregate_bool = False

						if aggregate_bool:

							# Generate and aggregate observation
							obs = faaclib.AggregatedObservation(record, FEATURES[source], Keys)
							obsBatch.add(obs)


			# Save output in a dictionary of dictionaries
			OBSERVATIONS[source][tag] = obsBatch



	# Fuse output observation from all datasources
	# ============================================


	# Extract all the possible tags from the observations
	TAGS = []
	for source in OBSERVATIONS:
		for tag in OBSERVATIONS[source]:
			if not tag in TAGS:
				TAGS.append(tag)
	

	# Dictionary of output observations by tag
	out_observations = {}

	# iterate through all possible tags.
	for tag in TAGS:

		# If there are keys, out_observation is a dictionary of dictionaries.
		if Keys:
			out_observations[tag]={}

		for source in OBSERVATIONS:
			if tag in list(OBSERVATIONS[source].keys()):

				# if the tag is alreaady added to the diccionary aggregate the observations
				if tag in out_observations:
					if Keys:
						for key in OBSERVATIONS[source][tag].observations:
							if key in out_observations[tag]:	
								out_observations[tag][key].aggregate(OBSERVATIONS[source][tag].observations[key])
							else:
								out_observations[tag][key] = OBSERVATIONS[source][tag].observations[key]
					else:
						out_observations[tag].aggregate(OBSERVATIONS[source][tag].observations[None]) 
				
				# If the tag is not in the observation add the first observation
				else:
					if Keys:
						for key in OBSERVATIONS[source][tag].observations:
							out_observations[tag][key] = OBSERVATIONS[source][tag].observations[key]

					else:
						out_observations[tag] = OBSERVATIONS[source][tag].observations[None]


	
	# Padding with 0s to easily form a matrix of observations afterwards

	for tag in out_observations:
		if Keys:
			for key in out_observations[tag]:
				out_observations[tag][key].zeroPadding(features)
		else:
			out_observations[tag].zeroPadding(features)



	# Delete temporal files
	# =====================

	if not (parserConfig['SPLIT']['Time']['window'] == None or parserConfig['SPLIT']['Time']['start'] == None or parserConfig['SPLIT']['Time']['end'] == None):

		print("\n\n\nRemoving temporal files...")
		shutil.rmtree(parserConfig['SPLIT']['Output'], ignore_errors=True)
	
	if delete_nfcsv:
		for file in delete_nfcsv:
			os.remove(file)

	# Write outputs
	# ==============

	print("\n-----------------------------------------------------------------------\n")
	print("Writing outputs...\n")
	print(("Elapsed: %s" %(prettyTime(time.time() - startTime))))


	if not Keys:

		# Write headers file with features.
		outstream = open(OUTDIR + 'headers.dat', 'w')
		next(iter(list(out_observations.values()))).writeLabels(outstream)
		outstream.close()
		
		# Write observation arrays
		for tag in out_observations:
			if out_observations[tag]:
				outpath = OUTDIR + 'output-' + tag + '.dat'
				outstream = open(outpath, 'w')
				out_observations[tag].writeValues(outstream)
				outstream.close()
			else:
				print(("  Aggregate %s(EMPTY-OUTPUT)" %("".ljust(32))))

	else:

		# Write headers file with features.
		outstream = open(OUTDIR + 'headers.dat', 'w')
		next(iter(list(out_observations.values()))).next(itervalues()).writeLabels(outstream)
		outstream.close()

		# Write observation arrays		
		for tag in out_observations:
			if out_observations[tag]:
				outpath = OUTDIR + 'output-' + tag + '.dat'
				outstream = open(outpath, 'w')

				outstream.write('\n KEYS: ' + str(Keys) + '\n\n')

				for key in out_observations[tag]:
					outstream.write(str(key) + ' --> ')
					out_observations[tag][key].writeValues(outstream)
					outstream.write('\n')

				outstream.close()


	print("\n-----------------------------------------------------------------------\n")
	print(("Finished: " + str(count_total) + " files analyzed "))



	# 5. Write stats

	print("Writing stats...\n")

	total_lines = 0
	total_unused_lines = 0
	total_files = 0

	statsStream.write("Lines, Unused lines, Files\n\n")

	for source in SOURCES:

		statsLine = source + " -->  " + str(stats['lines'][source]) + ", " +  str(stats['unused_lines'][source]) + ", " + str(len(SOURCES[source]['FILES']))
		statsStream.write(statsLine + '\n')
		
		total_lines += stats['lines'][source]
		total_unused_lines += stats['unused_lines'][source]
		total_files += len(SOURCES[source]['FILES'])
	
	statsStream.write("-------------------------------------------------\n\n")
	statsStream.write( "TOTAL -->  lines: "+ str(total_lines) + ", unused_lines: " + str(total_unused_lines) + ", files: " + str(total_files))
	statsStream.close()

	print(("Elapsed: %s" %(prettyTime(time.time() - startTime))))



	
def getTag(filename):
	tagSearch = re.search("(\w*)\.\w*$", filename)
	if tagSearch:
		return tagSearch.group(1)
	else:
		return None


def file_log_len(fname, separator):

	input_file = open(fname,'r')
	line = input_file.readline()
	count_log = 0

	if line:
		log ="" + line

		while line:
			log += line 

			if len(log.split(separator)) > 1:
				logExtract = log.split(separator)[0]
				count_log += 1		
				log = ""

				for n in logExtract.split(separator)[1::]:
					log += n

			line = input_file.readline()
		log += line
		
		if not log == "":
			count_log += 1 

	return count_log			

	
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
	stream = open(config_file, 'r')
	conf = yaml.load(stream)
	stream.close()
	return conf

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def getArguments():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description='''Multivariate Analysis Parsing Tool.''')
	parser.add_argument('config', metavar='CONFIG', help='Parser Configuration File.')
	args = parser.parse_args()
	return args


if __name__ == "__main__":
	
	main()
