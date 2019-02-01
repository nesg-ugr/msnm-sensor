#!/bin/bash
# This script copy the results of echa sensor in the <scenario>/results/

if [ "$#" -ne 1 ]; then
  echo " "
  echo "Use: ./copy_results.sh <path_escenario>"
  echo "Example of use:"
  echo "<path_escenario>: config/scenario_4/"
  echo " "
  exit 1
fi

#input params
path_scenario=$1

# list of sensors
sensor_list=`cat $path_scenario/sensors.txt`

# current dir
curr_dir=`pwd`

# ts
ts=`date +%Y%m%d_%H%M%S`

# results dir
results_d=$path_scenario/results/$ts

# check if the results dir exists
if [ ! -d "$results_d" ]; then
  echo "Creating results dir at $ts ..."
  mkdir -p $results_d
fi

# copy results
for i in $sensor_list;
do

  if [ ! -d "$results_d/$i" ]; then
    echo "Creating dir for sensor $i ..."
    mkdir -p $results_d/$i
  fi

  echo "Copying data of sensor $i ..."
  cp -r $path_scenario/$i/data/ $results_d/$i
done





