import hashlib
import random

from twisted.internet import defer
from twisted.python import log

from kademlia.protocol import KademliaProtocol
from kademlia.utils import deferredDict
from kademlia.storage import ForgetfulStorage
from kademlia.node import Node, NodeHeap


class SpiderCrawl(object):
        # call find_node to current ALPHA nearest not already queried,
        # ...adding results to current nearest
        # current nearest list needs to keep track of who has been queried already
        # sort by nearest, keep KSIZE
        # if list is same as last time, next call should be to everyone not
        # yet queried
        # repeat, unless nearest list has all been queried, then ur done
    
    def __init__(self, protocol, node, peers, ksize, alpha):
        self.protocol = protocol
        self.ksize = ksize
        self.alpha = alpha
        self.nearest = NodeHeap(self.ksize)
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
        count = self.alpha
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
        self.ksize = ksize
        self.alpha = alpha
        # 160 bit random id        
        rid = hashlib.sha1(str(random.getrandbits(255))).digest()
        storage = ForgetfulStorage()
        self.node = Node('127.0.0.1', port, rid)
        self.protocol = KademliaProtocol(self.node, storage, ksize, alpha)

    def bootstrap(self, addrs):
        def initTable(results):
            nodes = []
            for addr, result in results.items():
               if result[0]:
                   nodes.append(Node(addr[0], addr[1], result[1]))
            spider = SpiderCrawl(self.protocol, self.node, nodes, self.ksize, self.alpha)
            return spider.findNodes()

        ds = {}
        for addr in addrs:
            ds[addr] = self.protocol.ping(addr, self.node.id)
        return deferredDict(ds).addCallback(initTable)

    def get(self, key):
        node = Node(None, None, key)
        nearest = self.router.findNeighbors(node)
        spider = SpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.findValue()

    def set(self, key, value):
        # TODO - if no one responds, freak out
        def store(nodes):
            ds = [self.protocol.callStore(node) for node in nodes]
            return defer.gatherResults(ds)
        node = Node(None, None, key)
        nearest = self.router.findNeighbors(node)
        spider = SpiderCrawl(self.protocol, nearest, self.ksize, self.alpha)
        return spider.findNodes(node).addCallback(store)
