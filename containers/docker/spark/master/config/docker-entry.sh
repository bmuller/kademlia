#!/bin/bash

echo $MY_IP `hostname` >> /etc/hosts &&
/var/dht/spark-2.3.1-bin-hadoop2.7/sbin/start-master.sh --webui-port 8000; sleep infinity