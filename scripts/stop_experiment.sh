#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo " "
  echo "Use: ./stop_experiment.sh <path_escenario>"
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

# launch sensors
for i in $sensor_list;
do
  cd $curr_dir/$path_scenario/$i
  
  bash stop.sh
  
  cd $curr_dir
 
done

echo " "



