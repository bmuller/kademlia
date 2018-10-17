FROM ubuntu:18.04

RUN mkdir /var/spark

COPY containers/docker/spark/worker/config/ /var/spark/spark-worker-conf/
RUN find /var/spark/spark-worker-conf -type f -exec chmod 777 {} \;

ADD https://www.apache.org/dist/spark/spark-2.3.1/spark-2.3.1-bin-hadoop2.7.tgz /var/spark
RUN cd /var/spark && tar -xvzf spark-2.3.1-bin-hadoop2.7.tgz
RUN rm /var/spark/spark-2.3.1-bin-hadoop2.7.tgz

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python python-pip software-properties-common
RUN add-apt-repository ppa:webupd8team/java -y
RUN apt-get update
RUN echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections
RUN echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 seen true" | debconf-set-selections
RUN apt-get install -y oracle-java8-installer

RUN echo "JAVA_HOME=\"/usr/lib/jvm/java-8-oracle/jre\"" >> /etc/environment
RUN /bin/bash -c "source /etc/environment"

ENTRYPOINT ["sh", "/var/spark/spark-worker-conf/docker-entry.sh"]
