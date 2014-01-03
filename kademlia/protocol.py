from twisted.internet import log

from rpcudp.protocol import RPCProtocol
from kademlia.node import Node
from kademlia.routing import RoutingTable


class KademliaProtocol(RPCProtocol):
    def __init__(self, node, storage, ksize, alpha):
        RPCProtocol.__init__(self, node.port)
        self.router = RoutingTable(self)
        self.storage = storage
        self.sourceID = node.id

    def rpc_ping(self, sender, nodeid):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        return "pong"

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        self.storage[key] = value

    def rpc_find_node(self, sender, nodeid, key):
        source = Node(sender[0], sender[1], nodeid)
        self.router.addContact(source)
        return map(tuple, self.table.findNeighbors(Node(None, None, key))

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
        return d.addCallback(handleCallResponse, nodetoAsk)

    def callFindValue(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceID, nodeToFind.id)
        return d.addCallback(handleCallResponse, nodetoAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceID)
        return d.addCallback(handleCallResponse, nodetoAsk)

    def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.store(address, self.sourceID, key, value)
        return d.addCallback(handleCallResponse, nodetoAsk)

    def handleCallResponse(self, result):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if result[0]:
            self.router.addContact(node)
        else:
            self.router.removeContact(node)
        return result
