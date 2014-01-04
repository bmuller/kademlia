"""
Package for interacting on the network at a high level.
"""
import random

from twisted.internet.task import LoopingCall
from twisted.internet import defer, reactor

from kademlia.log import Logger
from kademlia.protocol import KademliaProtocol
from kademlia.utils import deferredDict, digest
from kademlia.storage import ForgetfulStorage
from kademlia.node import Node, NodeHeap


class SpiderCrawl(object):
    """
    Crawl the network and look for given 160-bit keys.
    """
    def __init__(self, protocol, node, peers, ksize, alpha):
        """
        Create a new C{SpiderCrawl}er.

        @param protocol: a C{KademliaProtocol} instance.
        @param node: A C{Node} representing the key we're looking for
        @param peers: A list of C{Node}s that provide the entry point for the network
        @param ksize: The value for k based on the paper
        @param alpha: The value for alpha based on the paper
        """
        self.protocol = protocol
        self.ksize = ksize
        self.alpha = alpha
        self.nearest = NodeHeap(self.ksize)
        self.node = node
        self.lastIDsCrawled = []
        self.log = Logger(system=self)
        self.log.info("creating spider with peers: %s" % peers)
        for peer in peers:
            self.nearest.push(self.node.distanceTo(peer), peer)

    def findNodes(self):
        """
        Find the closest nodes.
        """
        return self._find(self.protocol.callFindNode)

    def findValue(self):
        """
        Find either the closest nodes or the value requested.
        """
        def handle(result):
            if isinstance(result, dict):
                return result['value']
            return None
        d = self._find(self.protocol.callFindValue)
        return d.addCallback(handle)

    def _find(self, rpcmethod):
        """
        Get either a value or list of nodes.

        @param rpcmethod: The protocol's C{callfindValue} or C{callFindNode}.

        The process:
          1. calls find_* to current ALPHA nearest not already queried nodes,
             adding results to current nearest list of k nodes.
          2. current nearest list needs to keep track of who has been queried already
             sort by nearest, keep KSIZE
          3. if list is same as last time, next call should be to everyone not
             yet queried
          4. repeat, unless nearest list has all been queried, then ur done
        """
        count = self.alpha
        if self.nearest.getIDs() == self.lastIDsCrawled:
            self.log.info("last iteration same as current - checking all in list now")
            count = len(self.nearest)
        self.lastIDsCrawled = self.nearest.getIDs()

        ds = {}
        for peer in self.nearest.getUncontacted()[:count]:
            ds[peer.id] = rpcmethod(peer, self.node)
            self.nearest.markContacted(peer)
        return deferredDict(ds).addCallback(self._nodesFound)

    def _nodesFound(self, responses):
        """
        Handle the result of an iteration in C{_find}.
        """
        print "got some responses: ", responses
        toremove = []
        for peerid, response in responses.items():
            # response will be a tuple of (<response received>, <value>)
            # where <value> will be a list of tuples if not found or
            # a dictionary of {'value': v} where v is the value desired
            if not response[0]:
                toremove.push(peerid)
            elif isinstance(response[1], dict):
                self.log.debug("found value for %i" % self.node.long_id)
                return response[1]
            for nodeple in (response[1] or []):
                peer = Node(*nodeple)
                self.nearest.push(self.node.distanceTo(peer), peer)
        self.nearest.remove(toremove)

        if self.nearest.allBeenContacted():
            return list(self.nearest)
        return self.findNodes()


class Server(object):
    """
    High level view of a node instance.  This is the object that should be created
    to start listening as an active node on the network.
    """

    def __init__(self, ksize=20, alpha=3):
        """
        Create a server instance.  This will start listening on the given port.

        @param port: UDP port to listen on
        @param k: The k parameter from the paper
        @param alpha: The alpha parameter from the paper
        """
        self.ksize = ksize
        self.alpha = alpha
        self.log = Logger(system=self)
        storage = ForgetfulStorage()
        self.node = Node(None, None, digest(random.getrandbits(255)))
        self.protocol = KademliaProtocol(self.node.id, storage, ksize)
        self.refreshLoop = LoopingCall(self.refreshTable).start(3600)

    def listen(self, port):
        return reactor.listenUDP(port, self.protocol)

    def refreshTable(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        ds = []
        for id in self.protocol.getRefreshIDs():
            node = Node(None, None, id)
            nearest = self.protocol.router.findNeighbors(node, self.alpha)
            spider = SpiderCrawl(self.protocol, node, nearest)
            ds.append(spider.findNodes())
        return defer.gatherResults(ds)

    def bootstrap(self, addrs):
        """
        Bootstrap the server by connecting to other known nodes in the network.

        @param addrs: A C{list} of (ip, port) C{tuple}s
        """
        def initTable(results):
            nodes = []
            for addr, result in results.items():
                if result[0]:
                    nodes.append(Node(addr[0], addr[1], result[1]))
            spider = SpiderCrawl(self.protocol, self.node, nodes, self.ksize, self.alpha)
            return spider.findNodes()

        ds = {}
        for addr in addrs:
            ds[addr] = self.protocol.ping(addr, self.node.id)
        return deferredDict(ds).addCallback(initTable)

    def get(self, key):
        """
        Get a key if the network has it.

        @return: C{None} if not found, the value otherwise.
        """
        node = Node(None, None, digest(key))
        nearest = self.protocol.router.findNeighbors(node)
        spider = SpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.findValue()

    def set(self, key, value):
        """
        Set the given key to the given value in the network.

        TODO - if no one responds, freak out
        """
        self.log.debug("setting '%s' = '%s' on network" % (key, value))
        dkey = digest(key)

        def store(nodes):
            self.log.info("setting '%s' on %s" % (key, map(str, nodes)))
            ds = [self.protocol.callStore(node, dkey, value) for node in nodes]
            return defer.gatherResults(ds)

        node = Node(None, None, dkey)
        nearest = self.protocol.router.findNeighbors(node)
        spider = SpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.findNodes().addCallback(store)
