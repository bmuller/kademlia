import heapq
import time
import operator
from collections import OrderedDict

from kademlia.utils import OrderedSet, sharedPrefix


class KBucket(object):
    def __init__(self, rangeLower, rangeUpper, ksize):
        self.range = (rangeLower, rangeUpper)
        self.nodes = OrderedDict()
        self.replacementNodes = OrderedSet()
        self.touchLastUpdated()
        self.ksize = ksize

    def touchLastUpdated(self):
        self.lastUpdated = time.time()

    def getNodes(self):
        return self.nodes.values()

    def split(self):
        midpoint = (self.range[0] + self.range[1]) / 2
        one = KBucket(self.range[0], midpoint, self.ksize)
        two = KBucket(midpoint + 1, self.range[1], self.ksize)
        for node in self.nodes.values():
            bucket = one if node.long_id <= midpoint else two
            bucket.nodes[node.id] = node
        return (one, two)

    def removeNode(self, node):
        if node.id not in self.nodes:
            return

        # delete node, and see if we can add a replacement
        del self.nodes[node.id]
        if len(self.replacementNodes) > 0:
            newnode = self.replacementNodes.pop()
            self.nodes[newnode.id] = newnode

    def hasInRange(self, node):
        return self.range[0] <= node.long_id <= self.range[1]

    def isNewNode(self, node):
        return node.id not in self.nodes

    def addNode(self, node):
        """
        Add a C{Node} to the C{KBucket}.  Return True if successful,
        False if the bucket is full.

        If the bucket is full, keep track of node in a replacement list,
        per section 4.1 of the paper.
        """
        if node.id in self.nodes:
            del self.nodes[node.id]
            self.nodes[node.id] = node
        elif len(self) < self.ksize:
            self.nodes[node.id] = node
        else:
            self.replacementNodes.push(node)
            return False
        return True

    def depth(self):
        sp = sharedPrefix([n.id for n in self.nodes.values()])
        return len(sp)

    def head(self):
        return self.nodes.values()[0]

    def __getitem__(self, id):
        return self.nodes.get(id, None)

    def __len__(self):
        return len(self.nodes)


class TableTraverser(object):
    def __init__(self, table, startNode):
        index = table.getBucketFor(startNode)
        table.buckets[index].touchLastUpdated()
        self.currentNodes = table.buckets[index].getNodes()
        self.leftBuckets = table.buckets[:index]
        self.rightBuckets = table.buckets[(index + 1):]
        self.left = True

    def __iter__(self):
        return self

    def next(self):
        """
        Pop an item from the left subtree, then right, then left, etc.
        """
        if len(self.currentNodes) > 0:
            return self.currentNodes.pop()

        if self.left and len(self.leftBuckets) > 0:
            self.currentNodes = self.leftBuckets.pop().getNodes()
            self.left = False
            return self.next()

        if len(self.rightBuckets) > 0:
            self.currentNodes = self.rightBuckets.pop().getNodes()
            self.left = True
            return self.next()

        raise StopIteration


class RoutingTable(object):
    def __init__(self, protocol, ksize, node):
        """
        @param node: The node that represents this server.  It won't
        be added to the routing table, but will be needed later to
        determine which buckets to split or not.
        """
        self.node = node
        self.protocol = protocol
        self.ksize = ksize
        self.flush()

    def flush(self):
        self.buckets = [KBucket(0, 2 ** 160, self.ksize)]

    def splitBucket(self, index):
        one, two = self.buckets[index].split()
        self.buckets[index] = one
        self.buckets.insert(index + 1, two)

    def getLonelyBuckets(self):
        """
        Get all of the buckets that haven't been updated in over
        an hour.
        """
        return [b for b in self.buckets if b.lastUpdated < (time.time() - 3600)]

    def removeContact(self, node):
        index = self.getBucketFor(node)
        self.buckets[index].removeNode(node)

    def isNewNode(self, node):
        index = self.getBucketFor(node)
        return self.buckets[index].isNewNode(node)

    def addContact(self, node):
        index = self.getBucketFor(node)
        bucket = self.buckets[index]

        # this will succeed unless the bucket is full
        if bucket.addNode(node):
            return

        # Per section 4.2 of paper, split if the bucket has the node in its range
        # or if the depth is not congruent to 0 mod 5
        if bucket.hasInRange(self.node) or bucket.depth() % 5 != 0:
            self.splitBucket(index)
            self.addContact(node)
        else:
            self.protocol.callPing(bucket.head())

    def getBucketFor(self, node):
        """
        Get the index of the bucket that the given node would fall into.
        """
        for index, bucket in enumerate(self.buckets):
            if node.long_id < bucket.range[1]:
                return index

    def findNeighbors(self, node, k=None, exclude=None):
        k = k or self.ksize
        nodes = []
        for neighbor in TableTraverser(self, node):
            if neighbor.id != node.id and (exclude is None or not neighbor.sameHomeAs(exclude)):
                heapq.heappush(nodes, (node.distanceTo(neighbor), neighbor))
            if len(nodes) == k:
                break

        return map(operator.itemgetter(1), heapq.nsmallest(k, nodes))
