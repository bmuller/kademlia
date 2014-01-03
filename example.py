from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

log.startLogging(sys.stdout)

one = Server(1234)

def done(found):
    print "Found nodes: ", found
    reactor.stop()
two = Server(5678)
two.bootstrap([('127.0.0.1', 1234)]).addCallback(done)

reactor.run()
