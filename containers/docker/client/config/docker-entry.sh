#!/bin/bash

DEFAULT_KADEMLIA_PORT=8468
DEFAULT_API_PORT=8080

if [ -z "$CONNECT_IP" ]; then
  CONNECT_IP="127.0.0.1"
fi

if [ -z "$KADEMLIA_PORT" ]; then
  KADEMLIA_PORT=$DEFAULT_KADEMLIA_PORT
fi

if [ -z "$API_PORT" ]; then
  API_PORT=$DEFAULT_API_PORT
fi

if [ "$DEV" = true ] ; then
    apk add curl
fi


openssl genrsa -out key.pem 2048
openssl rsa -in key.pem -out public.pem -outform PEM -pubout

exec python /app/dht.py $CONNECT_IP $KADEMLIA_PORT $API_PORT