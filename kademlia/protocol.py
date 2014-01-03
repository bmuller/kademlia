from twisted.python import log

from rpcudp.protocol import RPCProtocol
from kademlia.node import Node
from kademlia.routing import RoutingTable


class KademliaProtocol(RPCProtocol):
    def __init__(self, node, storage, ksize, alpha):
        RPCProtocol.__init__(self, node.port)
        self.router = RoutingTable(self, ksize, alpha)
        self.storage = storage
        self.sourceID = node.id

    def rpc_ping(self, sender, nodeid):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        return self.sourceID

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        self.storage[key] = value

    def rpc_find_node(self, sender, nodeid, key):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        node = Node(None, None, key)
        return map(tuple, self.router.findNeighbors(node))

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
            self.router.addContact(node)
        else:
            self.router.removeContact(node)
        return result
