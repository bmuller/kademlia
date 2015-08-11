"""
Utility functions for tests.
"""
import os
import hashlib
from struct import pack

from kademlia.node import UnvalidatedNode, ValidatedNode, OwnNode
from kademlia.routing import RoutingTable


def mknode(id=None, ip=None, port=None, intid=None, intseed=None):
    """
    Make a node.  Created a random id if not specified.
    """
    if intid is not None:
        id = (pack('>l', intid), None)
    if not id and intseed is not None:
        id = OwnNode.restore(pack('>llllllll', 0, 0, 0, 0, 0, 0, 0, intseed)).id
    if not id:
        id = OwnNode.new().id
    return UnvalidatedNode(id, ip, port)


def mkValidatedNode():
    source = OwnNode.restore(pack('>llllllll', 0, 0, 0, 0, 0, 0, 0, 99))
    challenge = pack('>l', 311)
    response = source.completeChallenge(challenge)
    return ValidatedNode(source.id, challenge, response)


class FakeProtocol(object):
    def __init__(self, sourceNode, ksize=20):
        self.router = RoutingTable(self, ksize, sourceNode)
        self.storage = {}
        self.sourceID = sourceNode.id

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids

    def rpc_ping(self, sender, nodeid):
        source = ValidatedNode(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        return self.sourceID

    def rpc_store(self, sender, nodeid, key, value):
        source = ValidatedNode(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        self.log.debug("got a store request from %s, storing value" % str(sender))
        self.storage[key] = value

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = ValidatedNode(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        node = UnvalidatedNode((key, None))
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key):
        source = ValidatedNode(nodeid, sender[0], sender[1])
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
