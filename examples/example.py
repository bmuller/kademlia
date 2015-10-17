from __future__ import print_function

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server

log.startLogging(sys.stdout)

def done(result):
    print("Key result:", result)
    reactor.stop()

def setDone(result, server):
    server.get("a key").addCallback(done)

def bootstrapDone(found, server):
    server.set("a key", "a value").addCallback(setDone, server)

server = Server()
server.listen(8469)
bootstrap_nodes = [("127.0.0.1", 8468)]  # twistd -noy examples/server.tac
server.bootstrap(bootstrap_nodes).addCallback(bootstrapDone, server)

reactor.run()
