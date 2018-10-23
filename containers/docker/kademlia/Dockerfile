FROM python:3.7.0-alpine3.7

RUN apk add g++
RUN apk add make
RUN apk add libffi-dev
RUN apk add libressl-dev
COPY kademlia /app/kademlia
COPY setup.py /app
WORKDIR /app
RUN python3 setup.py sdist
RUN pip3 install -U --user dist/kademlia-1.1.tar.gz
RUN rm -rf /app