## Installation

To build images for containers run
```
docker build <path_to_dockerfile>
```

Then for running dht client containers use next commands:

for first container
```
docker run --name dht1 -p 8080:8080 <hash_of_build_docker_image>
```

for each next container
```
docker run --name <container_name ex. dht2> -e CONNECT_IP=<ip_of_first_container> <hash_of_build_docker_image>
```

For running spark master container run
```
docker run --name sm1 --hostname <spark_worker_hostname> -p 8000:8000 -e MY_IP=<running_node_ip> <hash_of_build_docker_image>
```

For running spark worker container run
```
docker run --name sw1 -p <spark_worker_port>:<spark_worker_port> -e MY_IP=<running_node_ip> -e MY_PORT=<spark_worker_port> -e MASTER_IP=<master_ip> -e MASTER_HOSTNAME=<master_hostname> <hash_of_build_docker_image>
```

## Usage

Each dht client container has API for keys get/set running on 8080 port. For dht1 container we used -p 8080:8080 for exposing that port. So now we are able to use http://<node_hostname>:8080 for setting and getting keys.

To set key:
```
POST http://localhost:8080/dht/<key>

BODY:
<value_json>
```

To get key:
```
GET http://localhost:8080/dht/<key>
```

Spark master webui is located on http://localhost:8000
Spark worker webui is located on http://localhost:<spark_worker_port>