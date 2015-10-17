import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from twisted.internet import reactor
from kademlia.network import Server

if os.path.isfile('cache.pickle'):
    kserver = Server.loadState('cache.pickle')
else:
    kserver = Server()
    kserver.bootstrap([("1.2.3.4", 8468)])
kserver.saveStateRegularly('cache.pickle', 10)
kserver.listen(8468)
reactor.run()
