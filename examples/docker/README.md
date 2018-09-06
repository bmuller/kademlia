## Installation

To build images for containers run
```
docker build .
```

Then for running containers use next commands:

for first container
```
docker run --name dht1 <hash_of_build_docker_image>
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

To connect to running container use
```
docker exec -it <container_name> bash
```
then you will be able to run scripts from the node

Files are stored in /var/dht.

There are sample scripts to add data and to read data.
To add asset data run
```
python3 add_asset.py $CONNECT_IP asset1 "{\"type\":\"test\"}"
```
To read data run
```
python3 add_asset.py $CONNECT_IP asset1
```