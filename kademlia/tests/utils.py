"""
Utility functions for tests.
"""
import random
import hashlib
from struct import pack

from kademlia.node import Node
from kademlia.routing import RoutingTable


def mknode(node_id=None, ip=None, port=None, intid=None):
    """
    Make a node.  Created a random id if not specified.
    """
    if intid is not None:
        node_id = pack('>l', intid)
    if not node_id:
        randbits = str(random.getrandbits(255))
        node_id = hashlib.sha1(randbits.encode()).digest()
    return Node(node_id, ip, port)


class FakeProtocol:
    def __init__(self, sourceID, ksize=20):
        self.router = RoutingTable(self, ksize, Node(sourceID))
        self.storage = {}
        self.sourceID = sourceID
