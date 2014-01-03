import random
import hashlib
from twisted.trial import unittest

from kademlia.node import Node, NodeHeap

class NodeTest(unittest.TestCase):
    def test_longID(self):
        rid = hashlib.sha1(str(random.getrandbits(255))).digest()
        n = Node(None, None, rid)
        self.assertEqual(n.long_id, long(rid.encode('hex'), 16))
