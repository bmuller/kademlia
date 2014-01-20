import random
import hashlib

from twisted.trial import unittest

from kademlia.node import Node, NodeHeap
from kademlia.tests.utils import mknode


class NodeTest(unittest.TestCase):
    def test_longID(self):
        rid = hashlib.sha1(str(random.getrandbits(255))).digest()
        n = Node(rid)
        self.assertEqual(n.long_id, long(rid.encode('hex'), 16))

    def test_distanceCalculation(self):
        ridone = hashlib.sha1(str(random.getrandbits(255)))
        ridtwo = hashlib.sha1(str(random.getrandbits(255)))

        shouldbe = long(ridone.hexdigest(), 16) ^ long(ridtwo.hexdigest(), 16)
        none = Node(ridone.digest())
        ntwo = Node(ridtwo.digest())
        self.assertEqual(none.distanceTo(ntwo), shouldbe)


class NodeHeapTest(unittest.TestCase):
    def test_maxSize(self):
        n = NodeHeap(mknode(intid=0), 3)
        self.assertEqual(0, len(n))

        for d in range(10):
            n.push(mknode(intid=d))
        self.assertEqual(3, len(n))

        self.assertEqual(3, len(list(n)))

    def test_iteration(self):
        heap = NodeHeap(mknode(intid=0), 5)
        nodes = [mknode(intid=x) for x in range(10)]
        for index, node in enumerate(nodes):
            heap.push(node)
        for index, node in enumerate(heap):
            self.assertEqual(index, node.long_id)
            self.assertTrue(index < 5)

    def test_remove(self):
        heap = NodeHeap(mknode(intid=0), 5)
        nodes = [mknode(intid=x) for x in range(10)]
        for node in nodes:
            heap.push(node)

        heap.remove([nodes[0].id, nodes[1].id])
        self.assertEqual(len(list(heap)), 5)
        for index, node in enumerate(heap):
            self.assertEqual(index + 2, node.long_id)
            self.assertTrue(index < 5)
