FROM kademlia:eqitii

COPY client /app
WORKDIR /app

COPY containers/docker/client/config/ /app/client-conf/
RUN find client-conf -type f -exec chmod 777 {} \;

RUN pip install -r requirements.txt

ENTRYPOINT ["sh","/app/client-conf/docker-entry.sh"]
