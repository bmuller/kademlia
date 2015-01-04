from twisted.trial import unittest

from kademlia.routing import KBucket
from kademlia.tests.utils import mknode, FakeProtocol


class KBucketTest(unittest.TestCase):
    def test_split(self):
        bucket = KBucket(0, 10, 5)
        bucket.addNode(mknode(intid=5))
        bucket.addNode(mknode(intid=6))
        one, two = bucket.split()
        self.assertEqual(len(one), 1)
        self.assertEqual(one.range, (0, 5))
        self.assertEqual(len(two), 1)
        self.assertEqual(two.range, (6, 10))

    def test_addNode(self):
        # when full, return false
        bucket = KBucket(0, 10, 2)
        self.assertTrue(bucket.addNode(mknode()))
        self.assertTrue(bucket.addNode(mknode()))
        self.assertFalse(bucket.addNode(mknode()))
        self.assertEqual(len(bucket), 2)

        # make sure when a node is double added it's put at the end
        bucket = KBucket(0, 10, 3)
        nodes = [mknode(), mknode(), mknode()]
        for node in nodes:
            bucket.addNode(node)
        for index, node in enumerate(bucket.getNodes()):
            self.assertEqual(node, nodes[index])

    def test_inRange(self):
        bucket = KBucket(0, 10, 10)
        self.assertTrue(bucket.hasInRange(mknode(intid=5)))
        self.assertFalse(bucket.hasInRange(mknode(intid=11)))
        self.assertTrue(bucket.hasInRange(mknode(intid=10)))
        self.assertTrue(bucket.hasInRange(mknode(intid=0)))


class RoutingTableTest(unittest.TestCase):
    def setUp(self):
        self.id = mknode().id
        self.protocol = FakeProtocol(self.id)
        self.router = self.protocol.router

    def test_addContact(self):
        self.router.addContact(mknode())
        self.assertTrue(len(self.router.buckets), 1)
        self.assertTrue(len(self.router.buckets[0].nodes), 1)
