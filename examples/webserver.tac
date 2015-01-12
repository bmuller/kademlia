from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.python import log
from twisted.internet import reactor, task
from twisted.web import resource, server
from twisted.web.resource import NoResource

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

application = service.Application("kademlia")
application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)

if os.path.isfile('cache.pickle'):
    kserver = Server.loadState('cache.pickle')
else:
    kserver = Server()
    kserver.bootstrap([("1.2.3.4", 8468)])
kserver.saveStateRegularly('cache.pickle', 10)

udpserver = internet.UDPServer(8468, kserver.protocol)
udpserver.setServiceParent(application)

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
        log.msg("Getting key: %s" % request.path.split('/')[-1])
        d = self.kserver.get(request.path.split('/')[-1])
        d.addCallback(respond)
        return server.NOT_DONE_YET

    def render_POST(self, request):
        key = request.path.split('/')[-1]
        value = request.content.getvalue()
        log.msg("Setting %s = %s" % (key, value))
        self.kserver.set(key, value)
        return value

website = server.Site(WebResource(kserver))
webserver = internet.TCPServer(8080, website)
webserver.setServiceParent(application)


# To test, you can set with:
# $> curl --data "hi there" http://localhost:8080/one
# and get with:
# $> curl http://localhost:8080/one
