#!/bin/bash


if [[ $EUID -ne 0 ]]; then
   echo "WARNING: Please run it as root ***" 1>&2
   exit 1
fi


iptables -F INPUT
iptables -F OUTPUT
iptables -F FORWARD

# Killing the process
killall nfcapd
