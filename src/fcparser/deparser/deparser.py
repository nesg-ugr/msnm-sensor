"""
parser -- This program take as input the features and the timestamps
obtaned fromdata analysis in order to extract the small amount of 
data related to anomalies in comparison to masive amounts of extracted data


Authors: Jose Manuel Garcia Gimenez (jgarciag@ugr.es)
		 
Last Modification: 29/Sep/2017

"""


import argparse
import time 
import os
import yaml
import glob
from datetime import datetime 
import re
from IPy import IP


def main():

	delete_nfcsv = None # bool variable for netflow raw data  

	startTime = time.time()

	# get config file from input arguments
	args = getArguments()

	# Check the config in yaml format
	try:
		deParserConfig = getConfiguration(args.config)
	except IOError:
		print("No such config file '%s'" %(args.config))
		exit(1)
	except yaml.scanner.ScannerError as e:
		print("Incorrect config file '%s'" %(args.config))
		print(e.problem)
		print(e.problem_mark)
		exit(1)
	try:
		dataSources = deParserConfig['DataSources']
		output = deParserConfig['Deparsing_output']
		threshold = output['threshold']
	except KeyError as e:
		print("Missing config key: %s" %(e.message))
		exit(1)

	# Sources settings	
	
	nfcapd_files = False
	sources_files = {}
	sources_config = {}
	tags = {}

	for source in dataSources:
		sources_files[source] = {}

		try:
			sources_config[source] = getConfiguration(dataSources[source]['config'])
			tags[source] = sources_config[source]['tag']
			sources_files[source]['files'] = glob.glob(dataSources[source]['data'])

			out_files = []
			for file in sources_files[source]['files']:
				if 'nfcapd' in file:

					out_file = '/'.join(file.split('/')[:-1]) + '/temp_' + file.split('.')[-1] + ""
					os.system("nfdump -r " + file + " -o csv >>"+out_file)
					os.system('tail -n +2 '+out_file + '>>' + out_file.replace('temp',source))
					os.system('head -n -3 ' + out_file.replace('temp',source) + ' >> ' + out_file.replace('temp',source) + '.csv')
					out_files.append(out_file.replace('temp',source) + '.csv')
					os.remove(out_file)
					os.remove(out_file.replace('temp',source))

					sources_files[source]['files'] = out_files
					delete_nfcsv = out_files

		except:
			print("Configuration file load error") 
			exit(1)

		# try:
		# 	nfcapd_files = glob.glob(dataSources[source]['nfcapd*'])
	
		# except:
		# 	print "No raw netflow files to deparse"

	# Dictionary of dictionaries with all the features from all the data sources.

	VARIABLES = {}
	FEATURES = {}
	structured = {}

	for source in sources_config:
		FEATURES[source] = {}
		VARIABLES[source] = {}
		structured[source] = sources_config[source]['structured']
 		for feature in sources_config[source]['FEATURES']:
 			try:
				FEATURES[source][feature['name']] = feature
			except:
				print("Cofiguration file error: missing features")
				exit(1)

 		for variable in sources_config[source]['VARIABLES']:
 			try:
				VARIABLES[source][variable['name']] = variable
			except:
				print("Cofiguration file error: missing vriables")
				exit(1)


	lines = {}
	for source in dataSources:
		lines[source] = 0
		
		if structured[source]:
			for file in sources_files[source]['files']:
				lines[source] += file_len(file)

		else:
			for file in sources_files[source]['files']:
				lines[source] += file_log_len(file,sources_config[source]['separator'])


	# Output settings
	try:
		OUTDIR = output['dir']
		if not OUTDIR.endswith('/'):
			OUTDIR = OUTDIR + '/'
	except (KeyError, TypeError):
		OUTDIR = 'OUTPUT/'
		print(" ** Default output directory: '%s'" %(OUTDIR))
	try:
		OUTSTATS = output['stats']
	except (KeyError, TypeError):
		OUTSTATS = 'stats.log'
		print(" ** Default log file: '%s'" %(OUTSTATS))

	# Create output directory and file

	if not os.path.exists(OUTDIR):
		os.mkdir(OUTDIR)
		print("** creating directory %s" %(OUTDIR))

	try:
		for source in dataSources:
			open(OUTDIR + "output_" + tags[source],'w') 
	except:
		print("error creating output file")
		exit(1)


	# Check input file, features and timestamp from the anomalies detected

	try:
		input_file = open(args.input, 'r')
	except IOError:
		print("No such input file '%s'" %(args.input))
		exit(1)


	# Check if the source files exist and are readable

	for source in sources_files:
		for source_file in sources_files[source]['files']:
			if source_file:
				try:
					stream = open(source_file,'r')
					stream.close()

				except IOError:
					print("No such config file '%s'" %(source_file))
					exit(1)
	

	#reverse tag dictionary to map tags into datasource files.
	inverse_tags = {v: k for k, v in list(tags.items())}
	
	#Extract features and timestams from the input file.
	line = input_file.readline()

	features = []
	timestamps = []
	featuresBol = False
	timeBol = False

	while line:
		if "features:" in line :
			featuresBol = True

		if "timestamps:" in line :
			timeBol = True
			featuresBol = False

		if featuresBol:
			try: 
				features.append(line.split("=")[1].strip())
			except:
				pass

		if timeBol:
			try: 
				timestamps.append(line.split("=")[1].strip())
			except:
				pass

		line = input_file.readline()



	# Print a summary of loaded parameters
	print("------------------------------------------------------------------------")
	print("Data Sources:")
	for source in sources_files:
				print("	- " + str(tags[source]) + " --> Files: " + str(sources_files[source]['files']))

	print("FEATURES:")
	print(" TOTAL " + (str(len(features))) + " features:  \n" + str(features) + "\n")
	print("------------------------------------------------------------------------\n")

	print("TIMESTAMPS")
	print(" TOTAL " + (str(len(timestamps))) + " timestamps:  \n" + str(timestamps) + "\n")
	print("------------------------------------------------------------------------\n")
	
	print("Output:")
	print("  Directory: %s" %(OUTDIR))
	print("  Stats file: %s" %(OUTSTATS))
	print("\n------------------------------------------------------------------------\n")
	print("Elapsed: %s" %(prettyTime(time.time() - startTime)))
	print("\n------------------------------------------------------------------------\n")



	# Change timestamps to search depending on the sampling frecuency
	try:
		sample_rate = deParserConfig['SPLIT']['Time']['window']

	except:
		print("Error configuration file: SPLIT")

	if not (sample_rate == 60  or sample_rate == None):
		temp = []
		for timestamp in timestamps:
			for i in range(sample_rate/60 ):
				t = datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S")
				t = t.replace(minute = t.minute + i)
				temp.append(str(t))

		timestamps = temp


	# # Generate outputs
	# ########################################################

	# # NFDUMP QUERIES FOR NETFLOW SOURCES

	# count_nf = 0
	
	# if nfcapd_files:
	# 	sFeatures = []	
	# 	feat_delete = []  # list of already deparsed features 

	# 	print "Nfdump queries... \n\n"
	# 	print " ** WARNING, errors may appear with nfdump queries, ignore that errors \n\n"

	# 	for feature in features:
	# 		if feature in FEATURES[inverse_tags['netflow']].keys():	
	# 			sFields_nfdump(FEATURES[inverse_tags['netflow']],sFeatures,feature)
	# 			feat_delete.append(feature)	

	# 			# delete already deparsed features form features list.

	# 	for f in feat_delete:
	# 		features.remove(f)

	# 	# append all the Variables with the conector and.

	# 	Variables = ""
	# 	for i in range(len(sFeatures) - 1):
	# 		Variables +=  sFeatures[i] + " and " 

	# 	if sFeatures:
	# 		Variables += sFeatures[-1]

	# 	# for each timestamp, generate the nfdump query with de filtering option extracted from the yaml file.
	# 	for timestamp in timestamps:
	# 		for file in  nfcapd_files:
	# 			if Variables:
	# 				count_nf += 1
	# 				date = parsedate(timestamp,sources_config[inverse_tags['netflow']]['timestamp_format'])
	# 				query = "nfdump -r " + file + ' -t ' + date + " '" + Variables +"' " + " >> " + OUTDIR + "output_" + tags[inverse_tags['netflow']] 

	# 				# print query
	# 				os.system(query)
	
	# 	dataSources.pop(inverse_tags['netflow'],None)

	# else:
	# 	print "No nfdump queries..."

	# print "\n---------------------------------------------------------------------------\n"
	# print "Elapsed: %s" %(prettyTime(time.time() - startTime))
	# print "\n---------------------------------------------------------------------------\n"


	##################################################################################################################################################################
	# Not Netflow datasources

	count_structured = 0
	count_unstructured = 0
	count_source = 0

	# iterate through features and timestams
	if features:
		for source in dataSources:
			print(source)
			
			count_source = 0
			tag = tags[source]
			sourcepath = sources_files[source]['files']
			formated_timestamps = format_timestamps(timestamps,sources_config[source]['timestamp_format'])

			# Structured sources
			# =========================================

			if structured[source]:
				output_file = open(OUTDIR + "output_" + tag,'w')
				# while count_source < lines[source]*0.01 and (not features_needed <= 0) : 
				feat_appear = {}
				for file in sourcepath:
					feat_appear[file] = []
					input_file = open(file,'r')
					line = input_file.readline()

					# First read to generate list of number of appearances
					while line:
						# try:
						t = getStructuredTime(line,0,sources_config[source]['timestamp_format'])		

						if str(t).strip() in formated_timestamps:
							# extract amount of features that appear in each line included in timestamps analyzed.
							feat_appear[file].append(search_amount_features(line,features,FEATURES[source],VARIABLES[source]))
						# except:
						#  	print "error"
								
						line = input_file.readline()
					input_file.close()


				# Obtain number of features needed to extract the log
				features_needed = len(features)
				count = 0
				while count < int(threshold) and (not features_needed <= 1):
					for file in feat_appear:
						count += feat_appear[file].count(int(features_needed))
					features_needed -= 1



				# Re-read the file
				for file in sourcepath:
					index = 0
					input_file = open(file,'r')
					input_file.seek(0)
					line = input_file.readline()
						
					while line:
						try:
							t = getStructuredTime(line,0,sources_config[source]['timestamp_format'])		
							if str(t).strip() in formated_timestamps:
								
								# Check if features appear in the log to write in the file.
								if feat_appear[file][index] >= features_needed:
									output_file.write(line + "\n")
									count_structured += 1	
								index += 1
						except:
							pass
						
						line = input_file.readline()
					input_file.close()
				output_file.close()


			# Unstructured sources
			# ==============================

			else:
				output_file = open(OUTDIR + "output_" + tag,'w')
	
				# while count_source < lines[source]*0.01 and (not features_needed <= 0) : 
				feat_appear = {}
				for file in sourcepath:
					feat_appear[file] = []
					input_file = open(file,'r')
					line = input_file.readline()


					# First read to generate list of number of appearances
					if line:
						log = "" + line 	
						while line:
							log += line 
				
							if len(log.split(sources_config[source]['separator'])) > 1:
								logExtract = log.split(sources_config[source]['separator'])[0]
								# For each log, extract timestamp with regular expresions and check if it is in the 
								# input timestamps
								try:
									t = getUnstructuredTime(logExtract, sources_config[source]['timestamp_regexp'], sources_config[source]['timestamp_format'])														
									if str(t).strip() in formated_timestamps:
										# Check if features appear in the log to write in the file.
										feat_appear[file].append(search_feature(FEATURES,VARIABLES,logExtract,features, source))
								except:
									pass
									
								log = ""
								for n in logExtract.split(sources_config[source]['separator'])[1::]:
									log += n
							line = input_file.readline()

						# Deal with the last log, not processed during while loop.
						log += line
						try:								
							t = getUnstructuredTime(log, sources_config[source]['timestamp_regexp'], sources_config[source]['timestamp_format'])
							if str(t) in timestamps:
								feat_appear[file].append(search_feature(FEATURES,VARIABLES,logExtract,features, source ))
						except:
							pass

					input_file.close()

				# Obtain number of features needed to extract the log
				features_needed = len(features)
				count = 0
				while count < int(threshold) and (not features_needed <= 1):
					for file in feat_appear:
						count += feat_appear[file].count(int(features_needed))
					features_needed -= 1

				# Re-read the file
				for file in sourcepath:
					index = 0
					input_file = open(file,'r')
					input_file.seek(0)
					line = input_file.readline()
						
					if line:
						log = "" + line 	
						while line:
							log += line 
							if len(log.split(sources_config[source]['separator'])) > 1:
								logExtract = log.split(sources_config[source]['separator'])[0]
								# For each log, extract timestamp with regular expresions and check if it is in the 
								# input timestamps
								try:
									t = getUnstructuredTime(logExtract, sources_config[source]['timestamp_regexp'], sources_config[source]['timestamp_format'])														
									if str(t).strip() in formated_timestamps:
										# Check if features appear in the log to write in the file.
										if feat_appear[file][index] >= features_needed:
											output_file.write(logExtract + "\n\n")
											count_unstructured += 1	
										index += 1
								except:
									pass

								log = ""
								for n in logExtract.split(sources_config[source]['separator'])[1::]:
									log += n
							line = input_file.readline()

					input_file.close()
				output_file.close()

			print("\n---------------------------------------------------------------------------\n")
			print("Elapsed: %s" %(prettyTime(time.time() - startTime)))
			print("\n---------------------------------------------------------------------------\n")

	stats( count_structured, count_unstructured, OUTDIR, OUTSTATS, startTime)

	if delete_nfcsv:
		for file in delete_nfcsv:
			os.remove(file)

def stats( count_structured, count_unstructured, OUTDIR, OUTSTATS, startTime):

	# Print stats
	print("\n---------------------------------------------------------------------------")	
	print("\nSearch finished:")
	print("Elapsed: %s" %(prettyTime(time.time() - startTime)))
	# print "\n Nfdump queries: " + str(count_nf)
	print(" Structured logs found:  " + str(count_structured))
	print(" Unstructured logs found: " + str(count_unstructured))
	print("\n---------------------------------------------------------------------------\n")

	# Write stats in stats.log file.
	try:
		stats_file = open(OUTDIR + OUTSTATS,'w')
		stats_file.write("STATS:\n")
		stats_file.write("---------------------------------------------------------------------------\n")
		# stats_file.write("Nfdump queries: " + str(count_nf) + "\n")
		stats_file.write(" Structured logs found: " + str(count_structured) + "\n")
		stats_file.write(" Unstructured logs found: " + str(count_unstructured))

	except IOError as e:
		print("Stats file error: " + e.msg())



def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


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



def search_feature(FEATURES,VARIABLES,logExtract,features,source):

	# Iterate through features, if all features of the given source appear in the log,


	feature_count = 0
	list_timetamps = []
	varBol = False		

	for feature in list(FEATURES[source].keys()):	
		if feature in features:			

			fVariable = FEATURES[source][feature]['variable']
		
			fValue = FEATURES[source][feature]['value']		
			fType = FEATURES[source][feature]['matchtype']		


			match = re.search(VARIABLES[source][fVariable]['where'],logExtract)

			if match:
				match = match.group()
				matchType = VARIABLES[source][fVariable]['matchtype']

				if fType == "regexp":
					if re.search(fValue, match):
						feature_count += 1
						varBol = True

				if fType == "single":	
					if str(fValue) == match:
						feature_count += 1
						varBol = True

				if fType == "multiple":
					if int(match) in fValue:
						feature_count += 1
						varBol = True

				if fType == "range":
					if int(match) >= fValue[0] and int(match) <= fValue[1]:
						feature_count += 1
						varBol = True



	return feature_count

# Fuction to parse date into YYYY-MM-DD hh:mm:ss 

def parsedate(timestamp, dateformat):

	# Method to change date format depending on the datasource
	# The format of each datasource is defined in the configuration file

	# output format. 
	# YYYY-MM-DD hh:mm:ss 		Example: 2012-04-05 23:31:00
	
	inDateformat = "%Y-%m-%d %H:%M:%S"
	return datetime.strptime(timestamp.strip(), inDateformat).strftime(dateformat)


def format_timestamps(timestamps, format2):

	timestamps_formated= []
	format1 = "%Y-%m-%d %H:%M:%S"

	for t in timestamps:
		timestamps_formated.append(str(datetime.strptime(t, format1).strftime(format2)))

	return timestamps_formated


def getArguments():

# Function to get input arguments using argparse.
# For more infor about the arguments, run deparser.py -h

	parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
	description='''Multivariate Analysis Deparsing Tool.''')
	parser.add_argument('config', metavar = 'CONFIG', help = 'Deparser Configuration File.')
	parser.add_argument('input', metavar = 'INPUT', help = 'Input file (vars and timestamps from multivariate analysis)')
	args = parser.parse_args()
	return args


def getConfiguration(config_file):

# Function to extract configurations from yaml files. 
# This info is stored into a dictionary.

	stream = file(config_file, 'r')
	conf = yaml.load(stream)
	stream.close()
	return conf



def prettyTime(elapsed):

# Function to change format of the time.

	hours = int(elapsed // 3600)
	minutes = int(elapsed // 60 % 60)
	seconds = int(elapsed % 60)
	pretty = str(seconds) + " secs"
	if minutes or hours:
		pretty = str(minutes) + " mins, " + pretty
	if hours:
		pretty = str(hours) + " hours, " + pretty
	return pretty



def getUnstructuredTime (log, patern, dateFormat):

# Fuction to extrat timestamp from an unstructured source

	p = re.search(patern,log)
	try:
		date_string = p.group(0)
		d = datetime.strptime(date_string,dateFormat)
		d = d.replace(second = 00)
		
		return d.strftime(dateFormat)
	except:
		return None

def getStructuredTime(line, pos, dateFormat):
	valueList = line.split(',')
	rawTime = valueList[pos].split('.')[0]
	time = datetime.strptime(rawTime, dateFormat)
	time = time.replace(second = 00)
	return time


def search_amount_features(line,features,FEATURES,VARIABLES):

	feature_count = 0

	for feature in features:

		try:
			fName = FEATURES[feature]['name']
			fVariable = FEATURES[feature]['variable']
			fType = FEATURES[feature]['matchtype']
			fValue = FEATURES[feature]['value']
			variable = VARIABLES[fVariable]
			pos = variable['where']

			line_split = line.split(',')

			if fType == 'regexp':		
				try:
					re.search(fValue, line_split[pos])
					feature_count += 1
				except:
					pass

			elif fType == 'single':		
				if line_split[pos].strip() == str(fValue):
					feature_count += 1

			elif fType == 'range':		

				start = fValue[0]
				end   = fValue[1]
				
				if (int(line_split[pos]) < end) and (int(line_split[pos]) > start):
					feature_count += 1 

			elif fType == 'multiple':
				for value in fValue:
					if line_split[pos] == value:
						feature_count += 1
		except:
		 	pass

	return feature_count


# def sFields_nfdump(nf_feat,sFeatures,feature):

# 	# Function to exrtact nfdump filters from features

# 	fName = nf_feat[feature]['name']
# 	fVariable = nf_feat[feature]['variable']
# 	fType = nf_feat[feature]['matchtype']
# 	fValue = nf_feat[feature]['value']


# 	# IP related features

# 	if fName.startswith('src_ip'):

# 		if fValue == "private":
# 			return "(src net 10.0.0.0/8 or src net 172.16.0.0/12 or src net 192.168.0.0/16)"

# 		if fValue == "public":
# 			return "not (src net 10.0.0.0/8 or src net 172.16.0.0/12 or src net 192.168.0.0/16)"

# 	elif fName.startswith('dst_ip'):

# 		if fValue == "public":
# 			return "not (dst net 10.0.0.0/8 or dst net 172.16.0.0/12 or dst net 192.168.0.0/16)"

# 		if fValue == "private":
# 			return "(dst net 10.0.0.0/8 or dst net 172.16.0.0/12 or dst net 192.168.0.0/16)"


# 	# Source port related features 

# 	if fName.startswith('sport'):

# 		if fType == 'single':
# 			sFeatures.append('src port '+ str(fValue))

# 		elif fType == 'multiple':
# 			for f in fValue:
# 				sFeatures.append('src port ' + str(f))

# 		elif fType == 'range':
# 			if isinstance(fValue, list) and len(fValue) == 2:
# 				start = fValue[0]
# 				end   = fValue[1]
# 				for f in range(start,end + 1):
# 					sFeatures.append('src port ' + str(f))


# 	# Destination port related features 

# 	elif fName.startswith('dport'):

# 		if fType == 'single':
# 			sFeatures.append('dst port '+ str(fValue))

# 		elif fType == 'multiple':
# 			for f in fValue:
# 				sFeatures.append('dst port ' + str(f))

# 		elif fType == 'range':
# 			if isinstance(fValue, list) and len(fValue) == 2:
# 				start = fValue[0]
# 				end   = fValue[1]
# 				for f in range(start,end + 1):
# 					sFeatures.append('dst port ' + str(f))


# 	# Protocol related features 

# 	elif fName.startswith('protocol'):
		
# 		if fType == 'single':
# 			sFeatures.append('proto '+ str(fValue).lower())


# 	# tcpflags  related features 

# 	elif fName.startswith('tcpflags'):
		
# 		if fType == 'regexp': 
# 			sFeatures.append('flags ' + fValue)


# 	# Type of service  related features 

# 	elif fName.startswith('srctos'):
		
# 		if fType == 'single':
# 			sFeatures.append('tos ' + str(fValue))


# 	# number of input and output packets related features 

# 	elif fName.startswith('in_npackets') or fName.startswith('out_npackets'):
		
# 		if fType == 'range':

# 			if isinstance(fValue, list) and len(fValue) == 2:
# 				start = fValue[0]
# 				end   = fValue[1]
				
# 				if start != 0 :
# 					start -1

# 				if end == 'Inf':
# 					sFeatures.append('packets > ' + str(start))

# 				else:
# 					sFeatures.append('(packets > ' + str(start) + ' and packets < ' + str(end+1) + ')')


# 	# number of input and output bytes related features 

# 	elif fName.startswith('in_nbytes') or fName.startswith('out_nbytes'):


# 		if fType == 'range':

# 			if isinstance(fValue, list) and len(fValue) == 2:
# 				start = fValue[0]
# 				end   = fValue[1]

# 				if start != 0 :
# 					start -1
				
# 				if end == 'Inf':
# 					sFeatures.append('bytes > ' + str(start))

# 				else:
# 					sFeatures.append('(bytes > ' + str(start) + ' and bytes < ' + str(end+1) + ')')


# 	# input interface  related features 

# 	elif fName.startswith('in_interface'):
		
# 		if fType == 'single':
# 			sFeatures.append('in if ' + str(fValue))


# 	# output interface  related features 

# 	elif fName.startswith('out_interface'):

# 		if fType == 'single':
# 			sFeatures.append('out if ' + str(fValue))


if __name__ == "__main__":
	main()
