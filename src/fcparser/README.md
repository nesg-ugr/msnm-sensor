
# FCParser

Parser for data streams composed of variate (structured and unstructured) sources.

Contact persons: José Camacho Páez (josecamacho@ugr.es)
		José Manuel García Jiménez (jgarciag@ugr.es)

Last modification of this document: 7/Jul/18


## Presentation

The FaaC parser library allows a comfortable, general and highly configurable parsing
of network data originating from different sources. It has been designed to transform
large amounts of heterogeneus network data into a single time-resolved stream of data
features suitable for the analysis with multivariate techniques and other machine 
learning tools, hopefully without losing relevant information in the process.

The parsing process is based on five steps:

1. SAMPLING the sources of data in user defined time intervals.
2. TRANSFORM the raw data into structured records with a number of variables.
3. AGGREGATE records according to specific criteria, defined by one or multiple aggre-
gation keys. If no key is specified, we aggregate all records per sampling interval 
and data source.
4. TRANSFORM aggregated record into observations, following the Feature as a Counter
approach, so that variables are tranformed into features defined as counters.
5. FUSE observations from different datasources.
   
To reach these goals, the analyst must provide expert knowledge on the data she wants
to analyze. The analyst must decide: which datasources to include and the sampling rate, 
which information is relevant to be stored as variables, which criteria should be used 
for the aggregation and what counters (features) should be defined. To this end, the 
FaaC parser library is highly configurable through configuration files in YAML format. 
Templates for these files can be found in the 'config' folder. 

																							
## Getting Started

We recommend adding the fcparser and deparser folders to the path. Please, have a look 
at the installation notes in the INSTALL file for additional steps.
														
### Parsing

1.- Configuration. First step is to build a configuration.yaml specifying the datasources 
and split setting. If split parameters are not determined, the data won't be sampled. See 
/config/configuration.yaml for more info. You can find a sampling configuration file in 
folder Example.

2.- Parse data. Extract observations from data.

In the example, data is sampled every 60s. Example usage:

	$ python <INSTALL_DIR>/fcparser/fcparser.py Example/config/configuration.yaml 

### Deparsing

1.- Configuration. The deparsing program uses the same configuration file used in the parsing 
process, see /config/configuration.yaml for more info.

2.- Deparsing. Extracts the logs related to anomalies. It takes as input features and timestamps.
See Example/deparsing_input to see the format of the input file.

	$ python <INSTALL_DIR>/deparser/deparser.py Example/config/configuration.yaml Example/deparsing_input 



## Summary

The present repository is organized as follows:

- INSTALL                 Intallation notes.
- fcparser/ 		          Python Module with all of the lib classes and main script to parser process.
- deparser/               Python script for the deparsing process.
- config/                 Templates of configuration files. 
- Example/		          Data and configuration for an example example.
	- Examples_data       Structured and unstructured data to test the tool.
	- config 			  Configuration files adapted to the provided data.


