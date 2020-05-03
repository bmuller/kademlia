from random import shuffle
from kademlia.routing import KBucket, TableTraverser


class TestKBucket:
    def test_split(self, mknode):  # pylint: disable=no-self-use
        bucket = KBucket(0, 10, 5)
        bucket.add_node(mknode(intid=5))
        bucket.add_node(mknode(intid=6))
        one, two = bucket.split()
        assert len(one) == 1
        assert one.range == (0, 5)
        assert len(two) == 1
        assert two.range == (6, 10)

    def test_split_no_overlap(self):  # pylint: disable=no-self-use
        left, right = KBucket(0, 2 ** 160, 20).split()
        assert (right.range[0] - left.range[1]) == 1

    def test_add_node(self, mknode):  # pylint: disable=no-self-use
        # when full, return false
        bucket = KBucket(0, 10, 2)
        assert bucket.add_node(mknode()) is True
        assert bucket.add_node(mknode()) is True
        assert bucket.add_node(mknode()) is False
        assert len(bucket) == 2

        # make sure when a node is double added it's put at the end
        bucket = KBucket(0, 10, 3)
        nodes = [mknode(), mknode(), mknode()]
        for node in nodes:
            bucket.add_node(node)
        for index, node in enumerate(bucket.get_nodes()):
            assert node == nodes[index]

    def test_remove_node(self, mknode):  # pylint: disable=no-self-use
        k = 3
        bucket = KBucket(0, 10, k)
        nodes = [mknode() for _ in range(10)]
        for node in nodes:
            bucket.add_node(node)

        replacement_nodes = bucket.replacement_nodes
        assert list(bucket.nodes.values()) == nodes[:k]
        assert list(replacement_nodes.values()) == nodes[k:]

        bucket.remove_node(nodes.pop())
        assert list(bucket.nodes.values()) == nodes[:k]
        assert list(replacement_nodes.values()) == nodes[k:]

        bucket.remove_node(nodes.pop(0))
        assert list(bucket.nodes.values()) == nodes[:k-1] + nodes[-1:]
        assert list(replacement_nodes.values()) == nodes[k-1:-1]

        shuffle(nodes)
        for node in nodes:
            bucket.remove_node(node)
        assert not bucket
        assert not replacement_nodes

    def test_in_range(self, mknode):  # pylint: disable=no-self-use
        bucket = KBucket(0, 10, 10)
        assert bucket.has_in_range(mknode(intid=5)) is True
        assert bucket.has_in_range(mknode(intid=11)) is False
        assert bucket.has_in_range(mknode(intid=10)) is True
        assert bucket.has_in_range(mknode(intid=0)) is True

    def test_replacement_factor(self, mknode):  # pylint: disable=no-self-use
        k = 3
        factor = 2
        bucket = KBucket(0, 10, k, replacementNodeFactor=factor)
        nodes = [mknode() for _ in range(10)]
        for node in nodes:
            bucket.add_node(node)

        replacement_nodes = bucket.replacement_nodes
        assert len(list(replacement_nodes.values())) == k * factor
        assert list(replacement_nodes.values()) == nodes[k + 1:]
        assert nodes[k] not in list(replacement_nodes.values())


# pylint: disable=too-few-public-methods
class TestRoutingTable:
    # pylint: disable=no-self-use
    def test_add_contact(self, fake_server, mknode):
        fake_server.router.add_contact(mknode())
        assert len(fake_server.router.buckets) == 1
        assert len(fake_server.router.buckets[0].nodes) == 1


# pylint: disable=too-few-public-methods
class TestTableTraverser:
    # pylint: disable=no-self-use
    def test_iteration(self, fake_server, mknode):
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
        fake_server.router.buckets = buckets

        # expected nodes order
        expected_nodes = [nodes[5], nodes[4], nodes[3], nodes[2], nodes[7],
                          nodes[6], nodes[1], nodes[0], nodes[9], nodes[8]]

        start_node = nodes[4]
        table_traverser = TableTraverser(fake_server.router, start_node)
        for index, node in enumerate(table_traverser):
            assert node == expected_nodes[index]
