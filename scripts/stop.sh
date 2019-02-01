#!/bin/bash

# This scripts is in charge of the gracefull stopping of the sensor.

# current dir

echo "Killing sensor with PID=`cat pid.txt`"

# stopping the sensor
kill -n SIGINT `cat pid.txt`

