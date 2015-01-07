from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

log.startLogging(sys.stdout)

if len(sys.argv) != 4:
    print "Usage: python query.py <bootstrap ip> <bootstrap port> <key>"
    sys.exit(1)

ip = sys.argv[1]
port = int(sys.argv[2])
key = sys.argv[3]

print "Getting %s (with bootstrap %s:%i)" % (key, ip, port)

def done(result):
    print "Key result:"
    print result
    reactor.stop()

def bootstrapDone(found, server, key):
    if len(found) == 0:
        print "Could not connect to the bootstrap server."
        reactor.stop()
    server.get(key).addCallback(done)

server = Server()
server.listen(port)
server.bootstrap([(ip, port)]).addCallback(bootstrapDone, server, key)

reactor.run()
