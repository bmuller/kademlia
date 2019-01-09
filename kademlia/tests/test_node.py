import unittest
import random
import hashlib


from kademlia.node import Node, NodeHeap
from kademlia.tests.utils import mknode


class NodeTest(unittest.TestCase):
    def test_long_id(self):
        rid = hashlib.sha1(str(random.getrandbits(255)).encode()).digest()
        node = Node(rid)
        self.assertEqual(node.long_id, int(rid.hex(), 16))

    def test_distance_calculation(self):
        ridone = hashlib.sha1(str(random.getrandbits(255)).encode())
        ridtwo = hashlib.sha1(str(random.getrandbits(255)).encode())

        shouldbe = int(ridone.hexdigest(), 16) ^ int(ridtwo.hexdigest(), 16)
        none = Node(ridone.digest())
        ntwo = Node(ridtwo.digest())
        self.assertEqual(none.distance_to(ntwo), shouldbe)


class NodeHeapTest(unittest.TestCase):
    def test_max_size(self):
        node = NodeHeap(mknode(intid=0), 3)
        self.assertEqual(0, len(node))

        for digit in range(10):
            node.push(mknode(intid=digit))
        self.assertEqual(3, len(node))

        self.assertEqual(3, len(list(node)))

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
