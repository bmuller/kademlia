#!/bin/bash

SLAVE_SCRIPT="/var/dht/spark-2.3.1-bin-hadoop2.7/sbin/start-slave.sh"
MASTER_SCRIPT="/var/dht/spark-2.3.1-bin-hadoop2.7/sbin/start-master.sh"

if [[ -z "${CONNECT_IP}" ]]; then
  bash $MASTER_SCRIPT --webui-port 8000
else
  bash $SLAVE_SCRIPT spark://$CONNECT_IP:7077
fi
