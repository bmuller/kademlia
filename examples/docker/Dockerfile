FROM ubuntu:18.04

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3 python3-pip git
RUN pip3 install asyncio
RUN pip3 install rpcudp
RUN pip3 install pickledb
RUN pip3 install aiohttp
RUN pip3 install cchardet
RUN pip3 install aiodns

RUN mkdir /var/dht
RUN cd /var/dht && git clone https://github.com/iotcoop/eqitii-dht

COPY dht.py /var/dht
COPY add_asset.py /var/dht
COPY read_asset.py /var/dht

CMD ["sh", "-c", "cd /var/dht && python3 dht.py $CONNECT_IP"]
