import random

from rpcudp.protocol import RPCProtocol
from kademlia.node import Node
from kademlia.routing import RoutingTable
from kademlia.log import Logger


class KademliaProtocol(RPCProtocol):
    def __init__(self, node, storage, ksize):
        RPCProtocol.__init__(self, node.port)
        self.router = RoutingTable(self, ksize)
        self.storage = storage
        self.sourceID = node.id
        self.log = Logger(system=self)

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids

    def rpc_ping(self, sender, nodeid):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        return self.sourceID

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        self.log.debug("got a store request from %s, storing value" % str(sender))
        self.storage[key] = value

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        node = Node(None, None, key)
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return { 'value': value }

    def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_node(address, self.sourceID, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callFindValue(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceID, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceID)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.store(address, self.sourceID, key, value)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if result[0]:
            self.log.info("got response from %s, adding to router" % node)
            self.router.addContact(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result
