import random
import hashlib

from twisted.trial import unittest

from kademlia.node import Node, NodeHeap


class NodeTest(unittest.TestCase):
    def test_longID(self):
        rid = hashlib.sha1(str(random.getrandbits(255))).digest()
        n = Node(None, None, rid)
        self.assertEqual(n.long_id, long(rid.encode('hex'), 16))

    def test_distanceCalculation(self):
        ridone = hashlib.sha1(str(random.getrandbits(255)))
        ridtwo = hashlib.sha1(str(random.getrandbits(255)))

        shouldbe = long(ridone.hexdigest(), 16) ^ long(ridtwo.hexdigest(), 16)
        none = Node(None, None, ridone.digest())
        ntwo = Node(None, None, ridtwo.digest())
        self.assertEqual(none.distanceTo(ntwo), shouldbe)


class NodeHeapTest(unittest.TestCase):
    def test_maxSize(self):
        n = NodeHeap(3)
        self.assertEqual(0, len(n))
