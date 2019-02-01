## MSNM sensor in action

If you are interested on to test the MSNM sensor, just follow the next steps.
In the figure you can see the scenario that we are going to build. Four are the involved routers (R1-3, BR (Border Router)). All of them, 
has a MSNMSensor instance and a netflow data source active. The BR is 
in charge of gathering the information comming from the other on the lower hierarchy level (R1, R2 and R3). BR also computes
 new statistics (LbRtn, QbRtn) which are in turn obtained by joining all the data sources.

![Simple example functional architecture](examples/scenario_4/arquitectura.png "Functional architecture")

- Activate the python 2.7 environment (see [How to install](../README.md))
- Go into **scripts/netflow/** folder
- Execute ipt-netflow collector engine and iptables integration.

		$ sudo ./activateNetflow.sh

     Before that the following tools should be already installed. On the contrary, please install them.

	    $ clone git://github.com/aabc/ipt-netflow.git
	    $ sudo apt-get install nfdump

- Go into **examples/scenario_4/**
- Set the name of the sensors in *sensors.txt* (take a look at it)
- Configure the *\*.yaml* configuration files for every involved sensor. Noting that such files has to be the same found in *sensors.txt* file. 
Additionally, *fcp\*.yaml* files, must be also configured if different data sources from netflow are used 
(see documentation at FCParser project)
- Go into **scripts/** folder
- Run the experiment. The following command will also launch each sensor. Alternatively, you can also start each sensor one by one by running *./start.sh* script available at each sensor folder.

	   	$ ./start_experiment.sh ../examples/scenario_4

 NOTE: You can monitor how each sensor is working by inspecting config/scenario_4/<*sensorName*\>/logs/msnm.log

- Stop the experiment gracefully. This scripts stop all deployed sensors. Alternatively, you can also stop each sensor one by one by running *./stop.sh* script available at each sensor folder.

	   	$ ./stop_experiment.sh config/scenario_4

- Copy the results obtained. Just for backing up the generated data by each sensor

	   	$ ./copy_results.sh config/scenario_4

- Plotting the results. This scripts depicts the statistics evolution from the monitoring output of a specific sensor. Last two parameters are the upper control limits for each statistics.

	   	$./plot_statistics.py <path_to_data> <logscale> <ucld> <uclq> 
	   	$ Example: ./plot_statistics.py ./config/scenario_4/results/20180102_162727/borderRouter/data/monitoring/output/ True 9.8 204.5
