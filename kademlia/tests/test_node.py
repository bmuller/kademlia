import random
import hashlib


from kademlia.node import Node, NodeHeap


class TestNode:
    def test_long_id(self):  # pylint: disable=no-self-use
        rid = hashlib.sha1(str(random.getrandbits(255)).encode()).digest()
        node = Node(rid)
        assert node.long_id == int(rid.hex(), 16)

    def test_distance_calculation(self):  # pylint: disable=no-self-use
        ridone = hashlib.sha1(str(random.getrandbits(255)).encode())
        ridtwo = hashlib.sha1(str(random.getrandbits(255)).encode())

        shouldbe = int(ridone.hexdigest(), 16) ^ int(ridtwo.hexdigest(), 16)
        none = Node(ridone.digest())
        ntwo = Node(ridtwo.digest())
        assert none.distance_to(ntwo) == shouldbe


class TestNodeHeap:
    def test_max_size(self, mknode):  # pylint: disable=no-self-use
        node = NodeHeap(mknode(intid=0), 3)
        assert not node

        for digit in range(10):
            node.push(mknode(intid=digit))

        assert len(node) == 3
        assert len(list(node)) == 3

    def test_iteration(self, mknode):  # pylint: disable=no-self-use
        heap = NodeHeap(mknode(intid=0), 5)
        nodes = [mknode(intid=x) for x in range(10)]
        for index, node in enumerate(nodes):
            heap.push(node)
        for index, node in enumerate(heap):
            assert index == node.long_id
            assert index < 5

    def test_remove(self, mknode):  # pylint: disable=no-self-use
        heap = NodeHeap(mknode(intid=0), 5)
        nodes = [mknode(intid=x) for x in range(10)]
        for node in nodes:
            heap.push(node)

        heap.remove([nodes[0].id, nodes[1].id])
        assert len(list(heap)) == 5
        for index, node in enumerate(heap):
            assert index + 2 == node.long_id
            assert index < 5
