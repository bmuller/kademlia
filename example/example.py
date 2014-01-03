from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

log.startLogging(sys.stdout)

def quit(result):
    print "Key result:", result
    reactor.stop()

def get(result, server):
    reactor.stop()
    #return server.get("a key").addCallback(quit)

def done(found, server):
    log.msg("Found nodes: %s" % found)
    return server.set("a key", "a value").addCallback(get, server)
two = Server(5678)
two.bootstrap([('127.0.0.1', 1234)]).addCallback(done, two)

reactor.run()
