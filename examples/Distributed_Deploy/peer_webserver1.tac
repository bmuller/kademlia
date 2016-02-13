from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.python import log
from twisted.internet import reactor, task
from twisted.web import resource, server
from twisted.web.resource import NoResource

import sys, os
import json
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

application = service.Application("kademlia")
application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)

#if os.path.isfile('cache.pickle'):
#    kserver = Server.loadState('cache.pickle')
#else:
kserver = Server()
kserver.bootstrap([("192.168.33.10", 8468)])
#kserver.saveStateRegularly('cache.pickle', 10)

udpserver = internet.UDPServer(8468, kserver.protocol)
udpserver.setServiceParent(application)

"""
class WebResource(resource.Resource):
    def __init__(self, kserver):
        resource.Resource.__init__(self)
        self.kserver = kserver

    def getChild(self, child, request):
        return self

    def render_GET(self, request):

        def respond(value):
            value = value or NoResource().render(request)
            request.write(value)
            request.finish()

        def getDHT(key):
            log.msg("Getting key: %s" % key)
            d = self.kserver.get(key)
            d.addCallback(respond)

        def getNeighbours():
            log.msg("Getting neighbours list")
            respond(json.dumps(self.kserver.getKnowNeighbours()))

        reqMessage = request.path.split('/')
        if reqMessage[1] == 'dht':
            getDHT(reqMessage[2])
        elif reqMessage[1] == 'neighbours':
            getNeighbours()
        else:
            log.msg("Wrong Rest Call")
        return server.NOT_DONE_YET

    def render_POST(self, request):
        key = request.path.split('/')[-1]
        value = request.content.getvalue()
        # Process data
        log.msg("Setting %s = %s" % (key, value))
        self.kserver.set(key, value)
        return value
"""


# Web Resource:
# Root resource which is responsible for handling HTTP paths.
class WebResource(resource.Resource):
    def __init__(self, kserver):
        resource.Resource.__init__(self)
        self.kserver = kserver
        self.putChild('dht', ResourceDHTHandler(self.kserver))
        self.putChild('neighbours', NeighboursHandler(self.kserver))

    def getChild(self, path, request):
        return self


# DHT Resource:
# Handles requests to get resources from the DHT or post resources to it.
class ResourceDHTHandler(resource.Resource):
    def __init__(self, kserver):
        resource.Resource.__init__(self)
        self.kserver = kserver

    def getChild(self, path, request):
        return self

    def render_GET(self, request):
        def respond(value):
            value = value or NoResource().render(request)
            request.write(value)
            request.finish()

        key = request.path.split('/')[-1]
        log.msg("Getting key: %s" % key)
        d = self.kserver.get(key)
        d.addCallback(respond)
        return server.NOT_DONE_YET

    def render_POST(self, request):
        key = request.path.split('/')[-1]
        value = request.content.getvalue()
        # Process data
        log.msg("Setting %s = %s" % (key, value))
        self.kserver.set(key, value)
        return value


# Neighbours Resource:
# Handles requests to get known neighbors.
class NeighboursHandler(resource.Resource):
    def __init__(self, kserver):
        resource.Resource.__init__(self)
        self.kserver = kserver

    def getChild(self, path, request):
        return self

    def render_GET(self, request):
        def respond(value):
            value = value or NoResource().render(request)
            request.write(value)
            request.finish()

        log.msg("Getting neighbours list")
        respond(json.dumps(self.kserver.getKnowNeighbours()))
        return server.NOT_DONE_YET

website = server.Site(WebResource(kserver))
webserver = internet.TCPServer(8080, website)
webserver.setServiceParent(application)
