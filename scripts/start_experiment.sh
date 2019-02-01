#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo " "
  echo "Use: ./start_experiment.sh <path_escenario>"
  echo "Example of use:"
  echo "<path_escenario>: ../examples/scenario_4/"
  echo " "
  exit 1
fi

#input params
path_scenario=$1

# list of sensors
sensor_list=`cat $path_scenario/sensors.txt`
# current dir
curr_dir=`pwd`

# deleting all existing information
for i in $sensor_list;
do
  echo "[+] Deleting sensor $i ..."
  rm -r $path_scenario/$i
done

# setting up the environment
echo "[+] Setting up the environment in $path_scenario ..."
echo " "

for i in $sensor_list;
do
  # Copy sensor 
  echo "[+] Copy needed files for sensor $i ..."
  # Copy sensor core python files
  rsync -aAL ../src/ $path_scenario/$i  
  # Copy start stop scripts
  cp start.sh $path_scenario/$i
  cp stop.sh $path_scenario/$i
  
done

# setting up the sensors' configurations
echo "[+] Setting up the sensor's configuration in $path_scenario ..."
echo " "

for i in $sensor_list;
do
  echo "[+] Configuring sensor $i ..."
  mkdir $path_scenario/$i/config/
  cp $path_scenario/fcparser_configuration.yaml $path_scenario/fcparser_netflow.yaml $path_scenario/logging.yaml $path_scenario/$i/config/ 
  # Copy sensor config files
  cp $path_scenario/$i.yaml $path_scenario/$i/config/
  mv $path_scenario/$i/config/$i.yaml $path_scenario/$i/config/sensor.yaml
  # Create logs files path
  mkdir $path_scenario/$i/logs
  touch $path_scenario/$i/logs/msnm.log
  
done

# pids
pids=()

# launch sensors
for i in $sensor_list;
do
  cd $curr_dir/$path_scenario/$i/
  
  bash start.sh
  
  cd $curr_dir
  
done

echo "[+] Listing running processes ..."
echo " "
echo `ps -ef | grep msnmsensor`


echo " "



