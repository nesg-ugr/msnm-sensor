#!/bin/bash

# This scripts is in charge of starting the sensor and saving the PID for arterward stopping it

# launch sensor

python msnmsensor.py config/sensor.yaml &>/dev/null &
#python msnmsensor.py config/sensor.yaml &
pid=$!

echo "[+] Launching sensor with PID=$pid"
echo $pid > pid.txt 




