import random

from twisted.internet import defer

from rpcudp.protocol import RPCProtocol

from kademlia.node import (
    UnvalidatedNode, ValidatedNode, NodeValidationError, format_nodeid
)
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
    
    def _addContact(self, nodeid, sender):
        node = ValidatedNode(tuple(nodeid), sender[0], sender[1])
        def finish(response, challenge):
            if not response[0]:
                self.log.debug('No response challenging {}'.format(node))
                return
            try:
                node.validate(challenge, response[1])
            except NodeValidationError as e:
                self.log.info(e)
                return False
            self.log.debug('Verified new contact {}, adding'.format(node))
            self.router.addContact(node)
            return True
        if self.router.isNewNode(node):
            self.router.addContact(node)
            return defer.succeed(True)
        else:
            # TODO keep a lookup of pending challenges
            challenge = self.sourceNode.generateChallenge()
            self.log.debug('Sending challenge {:.6}~ to {}'.format(challenge.encode('hex'), sender))
            d = self.challenge(sender, challenge)
            d.addCallback(finish, challenge)
            return d

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        self._addContact(nodeid, sender)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key, value):
        d = self._addContact(nodeid, sender)
        def finish(result):
            if result:
                self.log.debug("got a store request from %s, storing value" % str(sender))
                self.storage[key] = value
        d.addCallback(finish)
        return True

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of {} in local table".format(format_nodeid(nodeid)))
        source = UnvalidatedNode(tuple(nodeid), sender[0], sender[1])
        self._addContact(nodeid, sender)
        node = UnvalidatedNode(tuple(key))
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key):
        self._addContact(nodeid, sender)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return { 'value': value }

    def rpc_challenge(self, sender, challenge):
        self.log.debug('Responding to challenge {:.6}~ from {}'.format(challenge.encode('hex'), sender))
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
            d = self._addContact(node.id, (node.ip, node.port))
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
