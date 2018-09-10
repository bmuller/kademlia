## Installation

To build images for containers run
```
docker build .
```

Then for running containers use next commands:

for first container
```
docker run --name dht1 -p 8080:8080 <hash_of_build_docker_image>
```

for each next container
```
docker run --name <container_name ex. dht2> -e CONNECT_IP=<ip_of_first_container> <hash_of_build_docker_image>
```

to get IP address of the first container just run next command
```
docker inspect --format '{{ .NetworkSettings.IPAddress }}' dht1
```

## Usage

Each container has API for keys get/set running on 8080 port. For dht1 container we used -p 8080:8080 for exposing that port to localhost. So now we are able to use http://localhost:8080 for setting and getting keys.

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