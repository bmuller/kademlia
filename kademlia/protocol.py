import random
import asyncio
import logging

from rpcudp.protocol import RPCProtocol

from kademlia.node import Node
from kademlia.routing import RoutingTable
from kademlia.utils import digest

log = logging.getLogger(__name__)


class KademliaProtocol(RPCProtocol):
    def __init__(self, sourceNode, storage, ksize):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            rid = random.randint(*bucket.range).to_bytes(20, byteorder='big')
            ids.append(rid)
        return ids

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        log.debug("got a store request from %s, storing '%s'='%s'",
                  sender, key.hex(), value)
        self.storage[key] = value
        return True

    def rpc_find_node(self, sender, nodeid, key):
        log.info("finding neighbors of %i in local table",
                 int(nodeid.hex(), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        node = Node(key)
        neighbors = self.router.findNeighbors(node, exclude=source)
        return list(map(tuple, neighbors))

    def rpc_find_value(self, sender, nodeid, key):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return {'value': value}

    async def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.find_node(address, self.sourceNode.id,
                                      nodeToFind.id)
        return self.handleCallResponse(result, nodeToAsk)

    async def callFindValue(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.find_value(address, self.sourceNode.id,
                                       nodeToFind.id)
        return self.handleCallResponse(result, nodeToAsk)

    async def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.ping(address, self.sourceNode.id)
        return self.handleCallResponse(result, nodeToAsk)

    async def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.store(address, self.sourceNode.id, key, value)
        return self.handleCallResponse(result, nodeToAsk)

    def welcomeIfNewNode(self, node):
        """
        Given a new node, send it all the keys/values it should be storing,
        then add it to the routing table.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        if not self.router.isNewNode(node):
            return

        log.info("never seen %s before, adding to router", node)
        for key, value in self.storage.items():
            keynode = Node(digest(key))
            neighbors = self.router.findNeighbors(keynode)
            if len(neighbors) > 0:
                last = neighbors[-1].distanceTo(keynode)
                newNodeClose = node.distanceTo(keynode) < last
                first = neighbors[0].distanceTo(keynode)
                thisNodeClosest = self.sourceNode.distanceTo(keynode) < first
            if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                asyncio.ensure_future(self.callStore(node, key, value))
        self.router.addContact(node)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if not result[0]:
            log.warning("no response from %s, removing from router", node)
            self.router.removeContact(node)
            return result

        log.info("got successful response from %s", node)
        self.welcomeIfNewNode(node)
        return result
