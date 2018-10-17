#!/bin/bash

DEFAULT_PORT=8081

if [ -z "$MY_PORT" ]; then
  MY_PORT=$DEFAULT_PORT
fi

echo $MY_IP `hostname` >> /etc/hosts &&
echo $MASTER_IP $MASTER_HOSTNAME >> /etc/hosts &&
/var/spark/spark-2.3.1-bin-hadoop2.7/sbin/start-slave.sh --webui-port $MY_PORT spark://$MASTER_IP:7077; sleep infinity