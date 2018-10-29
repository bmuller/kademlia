import json
import random
import asyncio
import logging

from rpcudp.protocol import RPCProtocol

from kademlia.config import Config
from kademlia.utils import digest, validate_authorization, check_new_value_valid
from kademlia.crawling import ValueSpiderCrawl
from kademlia.crypto import Crypto
from kademlia.dto.dto import Value, JsonSerializable
from kademlia.exceptions import UnauthorizedOperationException, InvalidSignException
from kademlia.node import Node
from kademlia.routing import RoutingTable

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

    async def rpc_store(self, sender, nodeid, key, value):
        log.debug("got a store request from %s, storing '%s'='%s'",
                  sender, key.hex(), value)

        try:
            des_value = Value.of_json(json.loads(value))
            if des_value.authorization is not None:
                validate_authorization(key, des_value)

            log.debug(f"Received value for key {key.hex()} is valid,"
                      f" going to retrieve values stored under key : {key.hex}")
            stored_value_json = await self.get(key)
            if stored_value_json is not None:
                stored_value = Value.of_json(json.loads(stored_value_json))
                check_new_value_valid(key, stored_value, des_value)

            source = Node(nodeid, sender[0], sender[1])
            self.welcomeIfNewNode(source)

            self.storage[key] = value

        except AssertionError:
            log.exception("Unable to store value, got value with unsupported format: %s", value)
            data = f"Received request to store data of unsupported protocol from node : " \
                   f"[IP : {sender[0]}, PORT: {sender[1]}]"
            value = Crypto.get_signed_value(key, data)
            self.storage[key] = json.dumps(JsonSerializable.__to_dict__(value))

        except UnauthorizedOperationException:
            log.exception("Unable to store value, unauthorized storing attempt")

        except InvalidSignException:
            log.exception("Signature is not valid")

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

    async def get(self, key):
        log.info("Looking up key %s", key)
        # if this node has it, return it
        if self.storage.get(key) is not None:
            return self.storage.get(key)
        node = Node(key)
        nearest = self.router.findNeighbors(node)
        if len(nearest) == 0:
            log.warning("There are no known neighbors to get key %s", key)
            return None

        spider = ValueSpiderCrawl(self, node, nearest, Config.K_SIZE, Config.ALPHA)
        return await spider.find()
