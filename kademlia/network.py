"""
Package for interacting on the network at a high level.
"""
import random
import pickle

from twisted.internet.task import LoopingCall
from twisted.internet import defer, reactor, task

from kademlia.log import Logger
from kademlia.protocol import KademliaProtocol
from kademlia.utils import deferredDict, digest
from kademlia.storage import ForgetfulStorage
from kademlia.node import Node
from kademlia.crawling import ValueSpiderCrawl
from kademlia.crawling import NodeSpiderCrawl


class Server(object):
    """
    High level view of a node instance.  This is the object that should be created
    to start listening as an active node on the network.
    """

    def __init__(self, ksize=20, alpha=3, id=None):
        """
        Create a server instance.  This will start listening on the given port.

        @param port: UDP port to listen on
        @param k: The k parameter from the paper
        @param alpha: The alpha parameter from the paper
        """
        self.ksize = ksize
        self.alpha = alpha
        self.log = Logger(system=self)
        self.storage = ForgetfulStorage()
        self.node = Node(id or digest(random.getrandbits(255)))
        self.protocol = KademliaProtocol(self.node, self.storage, ksize)
        self.refreshLoop = LoopingCall(self.refreshTable).start(3600)

    def listen(self, port):
        """
        Start listening on the given port.

        This is the same as calling:
        C{reactor.listenUDP(port, server.protocol)}
        """
        return reactor.listenUDP(port, self.protocol)

    def refreshTable(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        ds = []
        for id in self.protocol.getRefreshIDs():
            node = Node(id)
            nearest = self.protocol.router.findNeighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest)
            ds.append(spider.find())

        def republishKeys(_):
            ds = []
            # Republish keys older than one hour
            for key, value in self.storage.iteritemsOlderThan(3600):
                ds.append(self.set(key, value))
            return defer.gatherResults(ds)

        return defer.gatherResults(ds).addCallback(republishKeys)

    def bootstrappableNeighbors(self):
        """
        Get a C{list} of (ip, port) C{tuple}s suitable for use as an argument
        to the bootstrap method.

        The server should have been bootstrapped
        already - this is just a utility for getting some neighbors and then
        storing them if this server is going down for a while.  When it comes
        back up, the list of nodes can be used to bootstrap.
        """
        neighbors = self.protocol.router.findNeighbors(self.node)
        return [ tuple(n)[-2:] for n in neighbors ]

    def bootstrap(self, addrs):
        """
        Bootstrap the server by connecting to other known nodes in the network.

        @param addrs: A C{list} of (ip, port) C{tuple}s.  Note that only IP addresses
        are acceptable - hostnames will cause an error.
        """
        # if the transport hasn't been initialized yet, wait a second
        if self.protocol.transport is None:
            return task.deferLater(reactor, 1, self.bootstrap, addrs)

        def initTable(results):
            nodes = []
            for addr, result in results.items():
                if result[0]:
                    nodes.append(Node(result[1], addr[0], addr[1]))
            spider = NodeSpiderCrawl(self.protocol, self.node, nodes, self.ksize, self.alpha)
            return spider.find()

        ds = {}
        for addr in addrs:
            ds[addr] = self.protocol.ping(addr, self.node.id)
        return deferredDict(ds).addCallback(initTable)

    def inetVisibleIP(self):
        """
        Get the internet visible IP's of this node as other nodes see it.

        @return: An C{list} of IP's.  If no one can be contacted, then the
        C{list} will be empty.
        """
        def handle(results):
            ips = [ result[1][0] for result in results if result[0] ]
            self.log.debug("other nodes think our ip is %s" % str(ips))
            return ips

        ds = []
        for neighbor in self.bootstrappableNeighbors():
            ds.append(self.protocol.stun(neighbor))
        return defer.gatherResults(ds).addCallback(handle)

    def get(self, key):
        """
        Get a key if the network has it.

        @return: C{None} if not found, the value otherwise.
        """
        node = Node(digest(key))
        nearest = self.protocol.router.findNeighbors(node)
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to get key %s" % key)
            return defer.succeed(None)
        spider = ValueSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.find()

    def set(self, key, value):
        """
        Set the given key to the given value in the network.
        """
        self.log.debug("setting '%s' = '%s' on network" % (key, value))
        dkey = digest(key)

        def store(nodes):
            self.log.info("setting '%s' on %s" % (key, map(str, nodes)))
            ds = [self.protocol.callStore(node, dkey, value) for node in nodes]
            return defer.DeferredList(ds).addCallback(self._anyRespondSuccess)

        node = Node(dkey)
        nearest = self.protocol.router.findNeighbors(node)
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to set key %s" % key)
            return defer.succeed(False)
        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.find().addCallback(store)

    def _anyRespondSuccess(self, responses):
        """
        Given the result of a DeferredList of calls to peers, ensure that at least
        one of them was contacted and responded with a Truthy result.
        """
        for deferSuccess, result in responses:
            peerReached, peerResponse = result
            if deferSuccess and peerReached and peerResponse:
                return True
        return False

    def saveState(self, fname):
        data = { 'ksize': self.ksize,
                 'alpha': self.alpha,
                 'id': self.node.id,
                 'neighbors': self.bootstrappableNeighbors() }
        with open(fname, 'w') as f:
            pickle.dump(data, f)

    @classmethod
    def loadState(self, fname):
        with open(fname, 'r') as f:
            data = pickle.load(f)
        s = Server(data['ksize'], data['alpha'], data['id'])
        if len(data['neighbors']) > 0:
            s.bootstrap(data['neighbors'])
        return s

    def saveStateRegularly(self, fname, frequency=600):
        """
        @param fname: File to save retularly to
        @param frequencey: Frequency in seconds that the state
        should be saved.  By default, 10 minutes.
        """
        loop = LoopingCall(self.saveState, fname)
        loop.start(frequency)
        return loop
