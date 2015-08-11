import random

from twisted.internet import defer

from rpcudp.protocol import RPCProtocol

from kademlia.node import ValidatedNode, NodeValidationError
from kademlia.routing import RoutingTable
from kademlia.log import Logger
from kademlia.utils import digest


class KademliaProtocol(RPCProtocol):
    def __init__(self, sourceNode, storage, ksize):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode
        self.log = Logger(system=self)

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids
    
    def _addContact(self, nodeid, sender, challenge, response):
        node = ValidatedNode(tuple(nodeid), sender[0], sender[1])
        def finish(response, challenge):
            try:
                node.verify(challenge, response):
            except NodeValidationError as e:
                self.log.info(e)
                return False
            self.router.addContact(node)
            return True
        if self.router.popContact(node):
            self.router.addContact(node)
            return defer.succeed(True)
        else:
            # TODO keep a lookup of pending challenges
            if challenge is None:
                challenge = self.sourceNode.generateChallenge()
                d = self.challenge(sender, challenge)
                d.addCallback(finish, challenge)
                return d
            else:
                return defer.succeed(finish(challenge, response))

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        self._addContact(nodeid, sender, None, None)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key, value):
        d = self._addContact(nodeid, sender, None, None)
        def finish(result):
            if result:
                self.log.debug("got a store request from %s, storing value" % str(sender))
                self.storage[key] = value
        d.addCallback(finish)
        return True

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = UnvalidatedNode(nodeid, sender[0], sender[1])
        self._addContact(nodeid, sender, None, None)
        node = UnvalidatedNode((key, None))
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key):
        self._addContact(nodeid, sender, None, None)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return { 'value': value }

    def rpc_challenge(self, sender, challenge):
        return self.sourceNode.completeChallenge(challenge)

    def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_node(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callFindValue(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceNode.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.store(address, self.sourceNode.id, key, value)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def transferKeyValues(self, node):
        """
        Given a new node, send it all the keys/values it should be storing.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        ds = []
        for key, value in self.storage.iteritems():
            keynode = UnvalidatedNode((digest(key), None))
            neighbors = self.router.findNeighbors(keynode)
            if len(neighbors) > 0:
                newNodeClose = node.distanceTo(keynode) < neighbors[-1].distanceTo(keynode)
                thisNodeClosest = self.sourceNode.distanceTo(keynode) < neighbors[0].distanceTo(keynode)
            if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                ds.append(self.callStore(node, key, value))
        return defer.gatherResults(ds)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if result[0]:
            self.log.info("got response from %s, adding to router" % node)
            d = self._addContact(node.id, (node.ip, node.port), None, None)
            def transfer(result):
                if not result:
                    return
                if self.router.isNewNode(node):
                    self.transferKeyValues(node)
            d.addCallback(transfer)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result
