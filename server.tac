from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os, pickle
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log


if os.path.isfile('cache.pickle'):
    data = pickle.load(open('cache.pickle'))
    kserver = Server(id = data['id'])
    kserver.bootstrap(data['servers'])
else:
    kserver = Server()

application = service.Application("kademlia")
application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)
server = internet.UDPServer(8468, kserver.protocol)
server.setServiceParent(application)

def updateCache():
    data = { 'id': kserver.node.id, 'servers': kserver.bootstrappableNeighbors() }
    with open('cache.pickle', 'w') as f:
        pickle.dump(data, f)

task.LoopingCall(updateCache).start(5.0, False)
