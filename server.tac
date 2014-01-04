from twisted.application import service, internet
import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server

application = service.Application("kademlia")
kserver = Server()
server = internet.UDPServer(1234, kserver.protocol)
server.setServiceParent(application)
