FROM ubuntu:18.04

RUN mkdir /var/dht

COPY spark-2.3.1-bin-hadoop2.7.tgz /var/dht
RUN cd /var/dht && tar -xvzf spark-2.3.1-bin-hadoop2.7.tgz
RUN rm /var/dht/spark-2.3.1-bin-hadoop2.7.tgz

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3 python3-pip git default-jdk
RUN pip3 install asyncio
RUN pip3 install rpcudp
RUN pip3 install pickledb
RUN pip3 install aiohttp
RUN pip3 install cchardet
RUN pip3 install aiodns

RUN echo "JAVA_HOME=\"/usr/lib/jvm/java-11-openjdk-amd64\"" >> /etc/environment
RUN /bin/bash -c "source /etc/environment"
RUN cd /var/dht && git clone https://github.com/iotcoop/eqitii-dht

COPY dht.py /var/dht
COPY start_spark.sh /var/dht
RUN chmod 755 /var/dht/start_spark.sh

CMD ["sh", "-c", "cd /var/dht && ./start_spark.sh && python3 dht.py $CONNECT_IP"]
