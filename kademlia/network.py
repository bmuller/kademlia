import hashlib
import random
import heapq

from twisted.internet import log, defer

from kademlia.protocol import KademliaProtocol
from kademlia.utils import deferredDict
from kademlia.storage import ForgetfulStorage

ALPHA = 3

class NodeHeap(object):
    def __init__(self, maxsize):
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
            if not node.id in peerIDs:
                heapq.heappush(nheap, (distance, node))
        self.heap = nheap

    def allBeenContacted(self):
        return len(self.getUncontacted()) == 0

    def getIDs(self):
        return [n.id for n in self]

    def markContacted(self, node):
        self.contacted.add(node.id)

    def push(self, distance, node):
        heapq.heappush(self.heap, (distance, node))

    def __len__(self):
        return min(len(self.heap), self.maxsize)

    def __iter__(self):
        return iter(heapq.nsmallest(self.maxsize, self.heap))

    def getUncontacted(self):
        return [n for n in self if not n.id in self.contacted]


class SpiderCrawl(object):
        # call find_node to current ALPHA nearest not already queried,
        # ...adding results to current nearest
        # current nearest list needs to keep track of who has been queried already
        # sort by nearest, keep KSIZE
        # if list is same as last time, next call should be to everyone not
        # yet queried
        # repeat, unless nearest list has all been queried, then ur done
    
    def __init__(self, protocol, node, peers):
        self.protocol = protocol
        self.nearest = NodeHeap(KSIZE)
        self.node = node
        self.lastIDsCrawled = []
        for peer in peers:
            self.nearest.push(self.node.distanceTo(peer), peer)


    def findNodes(self):
        return self.find(self.protocol.callFindNode)        

    def findValue(self):
        def handle(result):
            if isinstance(result, dict):
                return result['value']
            return None
        d = self.find(self.protocol.callFindValue)
        return d.addCallback(handle)

    def find(self, rpcmethod):
        count = ALPHA
        if self.nearest.getIDs() == self.lastIDsCrawled:
            count = len(self.nearest)
        self.lastIDsCrawled = self.nearest.getIDs()
        
        ds = {}
        for peer in self.nearest.getUncontacted()[:count]:
            ds[peer.id] = rpcmethod(peer, self.node)
            self.nearest.markContacted(peer)
        return deferredDict(ds).addCallback(self.nodesFound)

    def nodesFound(self, responses):
        toremove = []
        for peerid, response in responses.items():
            # response will be a tuple of (<response received>, <value>)
            # where <value> will be a list of tuples if not found or
            # a dictionary of {'value': v} where v is the value desired
            if not response[0]:
                toremove.push(peerid)
            elif isinstance(response[1], dict):
                return response[1]
            for nodeple in (response[1] or []):
                peer = Node(*nodeple)
                self.nearest.push(self.node.distanceTo(peer), peer)
        self.nearest.remove(toremove)

        if self.nearest.allBeenContacted():
            return list(self.nearest)
        return self.findNodes()


class Server:
    def __init__(self, port, ksize=20, alpha=3):
        # 160 bit random id        
        rid = hashlib.sha1(str(random.getrandbits(255))).digest()
        storage = ForgetfulStorage()
        self.node = Node('127.0.0.1', port, rid)        
        self.prototcol = KademliaProtocol(self.node, storage, ksize, alpha)

    def bootstrap(self, nodes):
        nodes = [ Node(*n) for n in nodes ]
        spider = NetworkSpider(self.protocol, self.node, nodes)
        return spider.findNodes()

    def get(self, key):
        node = Node(None, None, key)
        nearest = self.router.findNeighbors(node, ALPHA)
        spider = NetworkSpider(self.protocol, node, nearest)
        return spider.findValue()

    def set(self, key, value):
        # TODO - if no one responds, freak out
        def store(nodes):
            ds = [self.protocol.callStore(node) for node in nodes]
            return defer.gatherResults(ds)
        node = Node(None, None, key)
        nearest = self.router.findNeighbors(node, ALPHA)
        spider = NetworkSpider(self.protocol, nearest)
        return spider.findNodes(node).addCallback(store)
