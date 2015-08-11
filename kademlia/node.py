from operator import itemgetter
import heapq
import json

import nacl.signing
import nacl.utils
from nacl.encoding import RawEncoder as rawenc

from kademlia.utils import digest


def format_nodeid(nodeid):
    return '{:.6}~, {:.6}~'.format(nodeid[0].encode('hex'), nodeid[1].encode('hex'))


class NodeValidationError(RuntimeError):
    pass


class Node:
    def __init__(self, id, ip=None, port=None, derived=False):
        if not derived:
            raise AssertionError('Node base class instantiated.')
        if not isinstance(id, tuple):
            raise AssertionError('Node id must be a tuple.')
        self.id = id
        self.ip = ip
        self.port = port
        self.long_id = long(id[0].encode('hex'), 16)

    def sameHomeAs(self, node):
        return self.ip == node.ip and self.port == node.port

    def distanceTo(self, node):
        """
        Get the distance between this node and another.
        """
        return self.long_id ^ node.long_id

    def __iter__(self):
        """
        Enables use of Node as a tuple - i.e., tuple(node) works.
        """
        return iter([self.id, self.ip, self.port])

    def __repr__(self):
        return repr([format_nodeid(self.id), self.ip, self.port])

    def __str__(self):
        return "%s:%s" % (self.ip, str(self.port))


class UnvalidatedNode(Node):
    def __init__(self, id, ip=None, port=None):
        Node.__init__(self, id, ip, port, True)


class ValidatedNode(Node):
    def __init__(self, id, ip=None, port=None):
        Node.__init__(self, id, ip, port, True)

    def validate(self, challenge, response):
        verify_key = nacl.signing.VerifyKey(self.id[1], encoder=rawenc)
        def fail():
            raise NodeValidationError(
                "Encountered host node ({}) with invalid id: {}".format(
                    self,
                    json.dumps({
                        'id': self.id[0].encode('hex'),
                        'preid': self.id[1].encode('hex'),
                        'challenge': challenge.encode('hex'),
                        'response': response.encode('hex'),
                    }, indent=4),
                ))
        try:
            verify_key.verify(challenge, response, encoder=rawenc)
        except nacl.exceptions.BadSignatureError:
            fail()
        if digest(self.id[1]) != self.id[0]:
            fail()


class OwnNode(Node):
    seed = None
    key = None

    @staticmethod
    def _finish_init(cls, seed):
        key = nacl.signing.SigningKey(seed, encoder=rawenc)
        verify_key = key.verify_key.encode(encoder=rawenc)
        self = cls((digest(verify_key), verify_key), None, None, True)
        self.seed = seed
        self.key = key
        return self

    @classmethod
    def new(cls):
        seed = nacl.utils.random()
        return OwnNode._finish_init(cls, seed)

    @classmethod
    def restore(cls, seed):
        return OwnNode._finish_init(cls, seed)

    def completeChallenge(self, challenge):
        return self.key.sign(challenge).signature

    def generateChallenge(self):
        return nacl.utils.random()


class NodeHeap(object):
    """
    A heap of nodes ordered by distance to a given node.
    """
    def __init__(self, node, maxsize):
        """
        Constructor.

        @param node: The node to measure all distnaces from.
        @param maxsize: The maximum size that this heap can grow to.
        """
        self.node = node
        self.heap = []
        self.contacted = set()
        self.maxsize = maxsize

    def remove(self, peerIDs):
        """
        Remove a list of peer ids from this heap.  Note that while this
        heap retains a constant visible size (based on the iterator), it's
        actual size may be quite a bit larger than what's exposed.  Therefore,
        removal of nodes may not change the visible size as previously added
        nodes suddenly become visible.
        """
        peerIDs = set(peerIDs)
        if len(peerIDs) == 0:
            return
        nheap = []
        for distance, node in self.heap:
            if node.id not in peerIDs:
                heapq.heappush(nheap, (distance, node))
        self.heap = nheap

    def getNodeById(self, id):
        for _, node in self.heap:
            if node.id == id:
                return node
        return None

    def allBeenContacted(self):
        return len(self.getUncontacted()) == 0

    def getIDs(self):
        return [n.id for n in self]

    def markContacted(self, node):
        self.contacted.add(node.id)

    def popleft(self):
        if len(self) > 0:
            return heapq.heappop(self.heap)[1]
        return None

    def push(self, nodes):
        """
        Push nodes onto heap.

        @param nodes: This can be a single item or a C{list}.
        """
        if not isinstance(nodes, list):
            nodes = [nodes]

        for node in nodes:
            if node not in self:
                distance = self.node.distanceTo(node)
                heapq.heappush(self.heap, (distance, node))

    def __len__(self):
        return min(len(self.heap), self.maxsize)

    def __iter__(self):
        nodes = heapq.nsmallest(self.maxsize, self.heap)
        return iter(map(itemgetter(1), nodes))

    def __contains__(self, node):
        for distance, n in self.heap:
            if node.id == n.id:
                return True
        return False

    def getUncontacted(self):
        return [n for n in self if n.id not in self.contacted]
