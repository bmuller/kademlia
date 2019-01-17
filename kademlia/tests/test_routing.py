import unittest

from random import shuffle
from kademlia.routing import KBucket, TableTraverser
from kademlia.tests.utils import mknode, FakeProtocol


class KBucketTest(unittest.TestCase):
    def test_split(self):
        bucket = KBucket(0, 10, 5)
        bucket.add_node(mknode(intid=5))
        bucket.add_node(mknode(intid=6))
        one, two = bucket.split()
        self.assertEqual(len(one), 1)
        self.assertEqual(one.range, (0, 5))
        self.assertEqual(len(two), 1)
        self.assertEqual(two.range, (6, 10))

    def test_add_node(self):
        # when full, return false
        bucket = KBucket(0, 10, 2)
        self.assertTrue(bucket.add_node(mknode()))
        self.assertTrue(bucket.add_node(mknode()))
        self.assertFalse(bucket.add_node(mknode()))
        self.assertEqual(len(bucket), 2)

        # make sure when a node is double added it's put at the end
        bucket = KBucket(0, 10, 3)
        nodes = [mknode(), mknode(), mknode()]
        for node in nodes:
            bucket.add_node(node)
        for index, node in enumerate(bucket.get_nodes()):
            self.assertEqual(node, nodes[index])

    def test_remove_node(self):
        k = 3
        bucket = KBucket(0, 10, k)
        nodes = [mknode() for _ in range(10)]
        for node in nodes:
            bucket.add_node(node)

        replacement_nodes = bucket.replacement_nodes
        self.assertEqual(list(bucket.nodes.values()), nodes[:k])
        self.assertEqual(list(replacement_nodes.values()), nodes[k:])

        bucket.remove_node(nodes.pop())
        self.assertEqual(list(bucket.nodes.values()), nodes[:k])
        self.assertEqual(list(replacement_nodes.values()), nodes[k:])

        bucket.remove_node(nodes.pop(0))
        self.assertEqual(list(bucket.nodes.values()), nodes[:k-1] + nodes[-1:])
        self.assertEqual(list(replacement_nodes.values()), nodes[k-1:-1])

        shuffle(nodes)
        for node in nodes:
            bucket.remove_node(node)
        self.assertEqual(len(bucket), 0)
        self.assertEqual(len(replacement_nodes), 0)

    def test_in_range(self):
        bucket = KBucket(0, 10, 10)
        self.assertTrue(bucket.has_in_range(mknode(intid=5)))
        self.assertFalse(bucket.has_in_range(mknode(intid=11)))
        self.assertTrue(bucket.has_in_range(mknode(intid=10)))
        self.assertTrue(bucket.has_in_range(mknode(intid=0)))


class RoutingTableTest(unittest.TestCase):
    def setUp(self):
        self.id = mknode().id  # pylint: disable=invalid-name
        self.protocol = FakeProtocol(self.id)
        self.router = self.protocol.router

    def test_add_contact(self):
        self.router.add_contact(mknode())
        self.assertTrue(len(self.router.buckets), 1)
        self.assertTrue(len(self.router.buckets[0].nodes), 1)


class TableTraverserTest(unittest.TestCase):
    def setUp(self):
        self.id = mknode().id  # pylint: disable=invalid-name
        self.protocol = FakeProtocol(self.id)
        self.router = self.protocol.router

    def test_iteration(self):
        """
        Make 10 nodes, 5 buckets, two nodes add to one bucket in order,
        All buckets: [node0, node1], [node2, node3], [node4, node5],
                     [node6, node7], [node8, node9]
        Test traver result starting from node4.
        """

        nodes = [mknode(intid=x) for x in range(10)]

        buckets = []
        for i in range(5):
            bucket = KBucket(2 * i, 2 * i + 1, 2)
            bucket.add_node(nodes[2 * i])
            bucket.add_node(nodes[2 * i + 1])
            buckets.append(bucket)

        # replace router's bucket with our test buckets
        self.router.buckets = buckets

        # expected nodes order
        expected_nodes = [nodes[5], nodes[4], nodes[3], nodes[2], nodes[7],
                          nodes[6], nodes[1], nodes[0], nodes[9], nodes[8]]

        start_node = nodes[4]
        for index, node in enumerate(TableTraverser(self.router, start_node)):
            self.assertEqual(node, expected_nodes[index])
