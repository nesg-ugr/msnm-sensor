"""

FaaC parser library -- classes and tools for parsing and processing raw network
data and preparing it for further multivariate analysis.

See README file to learn how to use FaaC parser library.

Authors: Alejandro Perez Villegas (alextoni@gmail.com)
		 Jose Manuel Garcia Gimenez (jgarciag@ugr.es)

Last Modification: 29/Jul/2017

"""

from datetime import datetime, timedelta
from IPy import IP
import time
import re


#-----------------------------------------------------------------------
# Variable Classes
#-----------------------------------------------------------------------

class Variable(object):
	"""Single piece of information contained in a raw record.
	
	This is an abstract class, and should not be directly instantiated. 
	Instead, use one of the subclasses, defined for each matchtype of variable:
	- StringVariable    (matchtype 'string')
	- NumberVariable    (matchtype 'number')
	- IpVariable        (matchtype 'ip')
	- TimeVariable      (matchtype 'time')
	- TimedeltaVariable (matchtype 'duration')
	- MultipleVariable  (matchtype 'multiple')
	
	Class Attributes:
		value -- The value of the variable.
	"""
	def __init__(self, raw_value):
		"""Class constructor.

		raw_value -- Single value, as it is read from the input.
		"""
		self.value = self.load(raw_value)

	def equals(self, raw_value):
		"""Compares this variable to a given value.
		Returns 1 if the comparison matches; 
		        0 otherwise.

		raw_value -- The value to compare with.
		"""
		value = self.load(raw_value)
		output = (self.value == value)
		if output:
			return 1
		else:
			return 0

	def belongs(self, start, end):
		"""Checks whether this variable belongs to an interval.
		Returns 1 if the variable's value belongs to the interval;
		        0 otherwise.
		
		start -- Initial value of the interval (inclusive).
		end   -- Final value of the interval (inclusive).
		         'None' value means infinite.
		"""
		start_value = self.load(start)
		end_value   = self.load(end)

		if self.value is None or start_value is None:
			output = False
		elif end_value is None:
			output = (self.value >= start_value)
		else:
			output = (self.value >= start_value and self.value <= end_value)

		return output
		

	def __repr__(self):
		"""Class default string representation.
		"""
		return self.value.__str__()


class StringVariable(Variable):
	"""Variable containing an alphanumeric value.
	"""
	
	def load(self, raw_value):
		"""Converts an input raw value into a string object.
		Returns: String, if the conversion succeeds;
		         None, if the string is empty or the conversion fails.

		raw_value -- The input raw value.
		"""
		if raw_value:
			try:
				value = str(raw_value).strip()
				if not value:
					value = None
			except:
				value = None
		else:
			value = None
		return value


class NumberVariable(Variable):
	"""Variable containing a number.
	"""

	def load(self, raw_value):
		"""Converts an input raw value into an integer number.
		Returns: Integer number, if the conversion succeeds;
		         None, if the conversion fails.

		raw_value -- The input raw value.
		"""
		try:
			value = int(raw_value)
		except:
			value = None
		return value

class RegexpVariable(Variable):
	"""Variable containing a regexp match.
	"""

	def load(self, raw_value):
		"""Converts an input regexp match into a string object.
		Returns: String, if the conversion succeeds;
		None, if the string is empty or the conversion fails.

		raw_value -- regexp match.
		"""
		if raw_value:
			try:
				value = str(raw_value).strip()
				if not value:
					value = None
			except:
				value = None
		else:
			value = None
		return value


class IpVariable(Variable):
	"""Variable containing an IP address.
	"""
		
	def equals(self, raw_value):
		"""Compares this IP address to a given one, OR
		Checks this IP address matchtype.
		Suported matchtypes: 'private', 'public'.
		
		raw_value -- Specific IP address, OR matchtype of IP.
		"""
		if self.value is None:
			output = False
		elif raw_value == 'private':
			output = (self.value.iptype() == 'PRIVATE')
		elif raw_value == 'public':
			output = (self.value.iptype() == 'PUBLIC')
		else:
			value = self.load(raw_value)
			output = (self.value == value)

		return output
		
	def load(self, raw_value):
		"""Converts an input raw value into a IP address.
		Returns: IP object, if the conversion succeeds;
		         None, if the conversion fails.

		raw_value -- The input raw value, representing a IP address
		             (eg. '192.168.1.1').
		"""
		try:
			ipaddr = IP(raw_value)
		except:
			ipaddr = None
		return ipaddr


class TimeVariable(Variable):
	"""Variable containing a timestamp value.
	"""
		
	def load(self, raw_value):
		"""Converts an input raw value into a timestamp.
		Returns: Datetime object, if the conversion succeeds;
		         None, if the conversion fails.

		raw_value -- The raw value, in string format (eg. '2014-12-20 15:01:02'),
		             or in milliseconds since Epoch  (eg. 1293581619000)
		"""
		if isinstance(raw_value, str):
			try:
				timestamp = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")
			except:
				timestamp = None
		else:
			try:
				timestamp = datetime.utcfromtimestamp(float(raw_value)/1000)
			except:
				timestamp = None
		return timestamp


class TimedeltaVariable(TimeVariable):
	"""Variable containing a time duration.
	The value is a timedelta object.
	"""
	def __init__(self, start_value, end_value):
		"""Class constructor.

		start_value -- Raw start timestamp.
		end_value   -- Raw end timestamp.
		"""
		start_time = super(TimedeltaVariable, self).load(start_value)      # Python3: super().__init__()
		end_time   = super(TimedeltaVariable, self).load(end_value)        # Python3: super().__init__()
		try:
			self.value = end_time - start_time
		except TypeError:
			self.value = None
	
	def load(self, raw_value):
		"""Converts an input raw value into a timedelta.
		Returns: Timedelta object, if the conversion succeeds;
		         None, if the conversion fails.

		raw_value -- The time duration, in seconds (eg. 3600),
		"""
		try:
			duration = timedelta(seconds = int(raw_value))
		except:
			duration = None
		return duration

	def __repr__(self):
		"""Default string representation: number of seconds
		"""
		if self.value is not None:
			return str(self.value.total_seconds())
		else:
			return str(None)


class MultipleVariable(object):
	"""Multiple variable. Contains a list of variables.
	"""
	def __init__(self, variable):
		"""Class constructor.

		variable -- Single variable, first in the list.
		"""
		self.value = []
		self.value.append(variable)
		
	def equals(self, raw_value):
		"""Counts the amount of variables that equal the given value.
		Returns the number of matches.

		raw_value -- Single value to compare with.
		"""
		count = 0
		for f in self.value:
			if f.equals(raw_value):
				count += 1
		return count
	
	def belongs(self, start, end):
		"""Counts the amount of variables that belong to the given interval.
		Returns the number of matches.

		start -- Initial value of the interval (inclusive).
		end   -- Final value of the interval (exclusive).
                 'None' value means infinite.
		"""
		count = 0
		for f in self.value:
			if f.belongs(start, end):
				count += 1
		return count
		
	def __repr__(self):
		"""Class default string representation.
		"""
		return self.value.__str__()


#-----------------------------------------------------------------------
# Record Classes
#-----------------------------------------------------------------------

class Record(object):
	"""Information record containing data variables.
	
	The variables are defined in the user conf file, section VARIABLES.
	Each variable will be later used to define one or more features.
	
	A record looks like this:
	{flow_id: '4485422', src_ip: '192.168.1.2', src_port: 80, ...}
	
	Class Attributes:
		variables -- Dictionary of variables, indexed by their name.
		
	"""
	def __init__(self, line, variables, structured):
		self.variables = {}
		
		# For structured sources
		if structured:
			raw_values = line.split(',')

			for v in variables:
				try:
					vType = v['matchtype']
					vName = v['name']
					vWhere  = v['where']
				except KeyError as e:
					raise ConfigError(self, "VARIABLES: missing config key (%s)" %(e.message))	
				try:
					vMult = v['mult']
				except KeyError:
					vMult = False
				
				# Validate name
				if vName:
					vName = str(vName)
				else:
					raise ConfigError(self, "VARIABLE: empty id in variable")

				# Validate arg
				try:
					if isinstance(vWhere, list) and len(vWhere) == 2:
						vValue = [raw_values[vWhere[0]], raw_values[vWhere[1]]]
					else:
						vValue = raw_values[vWhere]
				except (TypeError, IndexError) as e:
					raise ConfigError(self, "VARIABLES: illegal arg in '%s' (%s)" %(vName, e.message))

				except:
					vValue = None
				# Validate matchtype
				if vType == 'string':
					variable = StringVariable(vValue)
				elif vType == 'number':
					variable = NumberVariable(vValue)
				elif vType == 'ip':
					variable = IpVariable(vValue)
				elif vType == 'time':
					variable = TimeVariable(vValue)
				elif vType == 'duration':
					if isinstance(vvalue, list) and len(vValue) == 2:
						variable = TimedeltaVariable(vValue[0], vValue[1])
					else:
						raise ConfigError(self, "VARIABLES: illegal arg in %s (two-item list expected)" %(vName))
				else:
					raise ConfigError(self, "VARIABLES: illegal matchtype in '%s' (%s)" %(vName, vType))
					
				# Add variable to the record
				if vMult:
					self.variables[vName] = MultipleVariable(variable)
				else:
					self.variables[vName] = variable

		# For unstructured sources

		else:

			for v in variables:
				try:
					vName = v['name']
					vWhere = v['where']
					vMatchType = v['matchtype']
					if isinstance(vWhere,str):
						vType = 'regexp'

				except KeyError as e:
					raise ConfigError(self, "VARIABLES: missing config key (%s)" %(e.message))

				# Validate name
				if vName:
					vName = str(vName)
				else:
					raise ConfigError(self, "VARIABLE: empty id in variable")

				# Validate name
				if vWhere:
					vWhere = str(vWhere)
				else:
					raise ConfigError(self, "VARIABLE: empty arg in variable; regular expresion expected")

				# Validate matchtype
				if vType == 'regexp':

					try:
						
						p = re.search(vWhere,line)
						vValue = p.group()

						if vMatchType == 'string':
							variable = StringVariable(vValue)

						elif vMatchType == 'number':
							variable = NumberVariable(vValue)

						elif vMatchType == 'ip':
							variable = IpVariable(vValue)

						elif vMatchType == 'time':
							variable = TimeVariable(vValue)

						elif vMatchType == 'duration':
							if isinstance(vvalue, list) and len(vValue) == 2:
								variable = TimedeltaVariable(vValue[0], vValue[1])
							else:
								raise ConfigError(self, "VARIABLES: illegal arg in %s (two-item list expected)" %(vName))


					except:
						variable = None
				else:
					raise ConfigError(self, "VARIABLES: illegal matchtype in '%s' (%s)" %(vName, vMatchType))


				self.variables[vName] = variable
	
	def __repr__(self):
		return "<%s - %d variables>" %(self.__class__.__name__, len(self.variables))
		
	def __str__(self):
		return self.variables.__str__()


#-----------------------------------------------------------------------
# Observation Classes
#-----------------------------------------------------------------------

class Observation(object):
	"""Observation array containing data suitable for the analysis.
	
	An observation array represents one row of data, and consist of a
	number of instances of the defined features. A feature represents
	one column of data. Thus, the input of the multivariate analysis
	engine consist of a N-by-M data matrix (N observations, M features).
	
	The features are defined in the user conf file, section features.
	Each feature is a integer counter defined from a specific variable.
	
	An observation looks like this:
	[0, 1, 0, 0, 2, 0, 0, 0, 3, 1, 0, ...]

	Class Attributes:
		label -- Array of features names.
		data  -- Array of data values.

	"""
	def __init__(self, record, FEATURES, debug=None):
		"""Creates an observation from a record of variables.
		record    -- Record object.
		FEATURES -- List of features configurations.

		"""
		self.label = [None] * len(FEATURES)    # List of features names
		self.data  = [None] * len(FEATURES)    # Data array (counters)
		defaults = []		               # tracks default features
		
		for i in range(len(FEATURES)):
			try:
				fName  = FEATURES[i]['name']
				fVariable = FEATURES[i]['variable']
				fType  = FEATURES[i]['matchtype']
				fValue = FEATURES[i]['value']
			except KeyError as e:
				raise ConfigError(self, "FEATURES: missing config key (%s)" %(e.message))

			# Validate name
			if fName:
				fName = str(fName)
			else:
				raise ConfigError(self, "FEATURES: missing variable name")

			# Validate variable
			try:				
				variable = record.variables[fVariable]
			except KeyError as e:
				variable = None

			# Calculate feature 

			# Iterate through all the features in the conf file. For each iteration, check the matchtype of the variable 
			# involved. Then, check the value of the variable asociated to the feature. If there is a match, the counters
			# of the observations are increased. --> FaaC (Feature as a counter)

			counter = 0
			if variable:
				if fType == 'single':
					if isinstance(fValue, list):
						raise ConfigError(self, "FEATURES: illegal value in '%s' (single item expected)" %(fName))
					counter += variable.equals(fValue)

				elif fType == 'multiple':
					if isinstance(fValue, list):
						for v in fValue:
							counter += variable.equals(v)
					else:
						raise ConfigError(self, "FEATURES: illegal value in '%s' (list of items expected)" %(fName))

				elif fType == 'range':
					if isinstance(fValue, list) and len(fValue) == 2:
						start = fValue[0]
						end   = fValue[1]
						if str(end).lower() == 'inf':
							end = None
						counter += variable.belongs(start, end)
					else:
						raise ConfigError(self, "FEATURES: illegal value in '%s' (two-item list expected)" %(fName))
				
				elif fType == 'regexp':
					if isinstance(fValue, list):
						raise ConfigError(self, "FEATURES: illegal value in '%s' (single item expected)" %(fName))
					pattern = fValue
					try:
						matchObj = re.search(pattern, str(variable))
					except re.error as e:
						raise ConfigError(self, "FEATURES: illegal regexp in '%s' (%s)" %(fName, e.message))
					if matchObj:
						counter += 1
						
				elif fType == 'default':
					defaults.append(i)
				
				else:
					raise ConfigError(self, "FEATURES: illegal matchtype in '%s' (%s)" %(fName, fType))
				
			# Update data lists
			self.label[i] = fName
			self.data[i]  = counter

			# Show debug info
			if debug:
				if vType == 'regexp':
					print(("%s%s %d" %(fName.ljust(25), (str(variable) + " == " + str("r'" + vValue + "'")).ljust(30), counter)))
				else:
					print(("%s%s %d" %(fName.ljust(25), (str(variable) + " == " + str(vValue)).ljust(30), counter)))

		# Manage default variables
		for d in defaults:
			assigned = False
			for i in range(len(FEATURES)):
				if FEATURES[i]['variable'] == FEATURES[d]['variable']:
					if self.data[i] > 0:
						assigned = True
						break
			if not assigned:
				self.data[d] += 1
			
	def aggregate(self, obs):
		""" Aggregates this observation with a new one.
			obs -- Observation object to merge with.
		"""
		

		if self.label == obs.label:
			try:
				for i in range(len(self.data)):
					self.data[i] += obs.data[i]
			except IndexError as e:
				raise AggregateError (self, "Unable to aggregate data arrays (%s)" %(e.message))

		else:
			self.label += obs.label
			self.data += obs.data

	def formatCSV(self):
		"""Converts the observation to a string in CSV format.
		"""
		return ','.join([str(x) for x in self.data]) + '\n'

	def __repr__(self):
		return "<%s - %d vars>" %(self.__class__.__name__, len(self.data))
		
	def __str__(self):
		return self.data.__str__()


	def write(self, outstream):
		"""Writes the observations to a file.
		A header line preceded by '#' contains the variable names.
		Following, the observations are written in CSV format.
		"""

		headerLine = ', '.join(self.label) + '\n'
		outstream.write(headerLine)

		outstream.write(self.formatCSV())

	
	def writeLabels(self, outstream):
		"""Writes only the list of feature names 
		   in a line of the file
		"""

		headerLine = ', '.join(self.label) + '\n'
		outstream.write(headerLine)
	


	def writeValues(self, outstream):
		"""Writes only the values of the features 
		   in a line of the file
		"""

		outstream.write(self.formatCSV())


	
class AggregatedObservation(Observation):
	"""Observation array with an aggregation ID.
	
	This is an Observation subclass used to track aggregations.
	The aggregation ID is built based on the aggregation keys defined in
	the user conf file, section KEYS. 
	Empty (or absence of) keys means no aggregation.
	
	An aggregated observation looks like this:
	'150.200.41.1' --> [0, 1, 0, 0, 2, 0, 0, 0, 3, 1, 0, ...]

	Class Attributes:
		ID    -- ID of the observation.
		label -- Array of variable names.
		data  -- Array of data values.
		nObs  -- Number of observations aggregated.
	"""
	def __init__(self, record, FEATURES, keys):
		"""Creates an aggregated observation from a record of variables.
		
		record    -- Record object.
		FEATURES -- List of variable configurations.
		keys -- List of keys configurations.
		"""
		try:
			keys 
		except KeysError as e:
			keys = None
		try:
			if not keys:
				self.ID = None
			elif isinstance(keys, list):
				self.ID = ', '.join([str(record.variables[x].value) for x in keys])
			else:
				self.ID = record.variables[keys].value
		except KeyError as e:
			raise ConfigError(self, "KEYS: incorrect variable reference (%s)" %(e.message))

		super(AggregatedObservation, self).__init__(record, FEATURES)  # Python3: super().__init__()
		self.nObs = 1
		
	def aggregate(self, aggr_obs):
		"""Aggregates this observation with a new one.
		
		aggr_obs -- Aggregated-observation object to merge with.
		"""
		if self.ID == aggr_obs.ID:
			super(AggregatedObservation, self).aggregate(aggr_obs)      # Python3: super().aggregate()
			self.nObs += 1
		else:
			raise AggregateError(self, "Observation IDs don't match.")

	def __repr__(self):
		return "<%s - %d vars>" %(self.__class__.__name__, len(self.data))


	def zeroPadding(self, features):

		all_data = [0] * len(features)
		all_labels = features
		for feature in features:
			if feature in self.label:
				all_data[all_labels.index(feature)] = self.data[self.label.index(feature)]
			else:
				all_data[all_labels.index(feature)] = 0

		self.data = all_data
		self.label = all_labels


	
class ObservationBatch(object):
	"""Batch of observations.
	
	An observation batch contains all the aggregated observations
	produced at a time k.
	This is the output of the parsing process.

	Class Attributes:
		observations -- Dictionary of aggregated observations, indexed 
		                by their ID.
	"""
	def __init__(self):
		"""Creates an empty observation batch."""

		self.observations = {}

	def add(self, obs):
		"""Adds a new observation to the batch.
		If the ID already exists, the new observation is aggregated;
		otherwise it is added as new item.
		"""

		if obs.ID in self.observations:
			self.observations[obs.ID].aggregate(obs)
		else:
			self.observations[obs.ID] = obs

	def __str__(self):
		"""Prints nice representation of the batch
		"""
		s = ""
		if self.observations:
			firstKey = list(self.observations.keys())[0]
			col1 = len(str(len(self.observations))) + 2
			col2 = len(str(self.observations[firstKey].ID)) + 12
			col3 = len(str(self.observations[firstKey].nObs)) + 5
			count = 0
			for obsKey in self.observations:
				s += "#%s%s%s%s\n" %(str(count).ljust(col1), 
									 str(self.observations[obsKey].ID).ljust(col2),
									 str(self.observations[obsKey].nObs).ljust(col3),
									 self.observations[obsKey].__repr__())
				count += 1
		else:
			s = "<Empty-Observation-Batch>"
		return s



#-----------------------------------------------------------------------
# Exception and Error Classes
#-----------------------------------------------------------------------

class ConfigError(Exception):
	def __init__(self, obj, message=''):
		self.obj = obj
		self.message = message
		self.msg = "ERROR - Config File - %s" %(message)

class AggregateError(Exception):
	def __init__(self, obj, message=''):
		self.obj = obj
		self.message = message
		self.msg = "ERROR - Aggregate - %s" %(message)
