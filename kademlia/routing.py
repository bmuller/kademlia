import heapq
from collections import OrderedDict

from twisted.internet.task import LoopingCall

class KBucket(object):
    def __init__(self, rangeLower, rangeUpper):
        self.range = (rangeLower, rangeUpper)
        self.nodes = OrderedDict()
        self.touchLastUpdated()

    def touchLastUpdated(self):
        self.lastUpdated = time.time()

    def getNodes(self):
        return self.nodes.values()

    def split(self):
        midpoint = self.range[1] - ((self.range[1] - self.range[0]) / 2)
        one = KBucket(self.range[0], midpoint)
        two = KBucket(midpoint+1, self.range[1])
        for node in self.nodes.values():
            bucket = one if node.long_id <= midpoint else two
            bucket.nodes[node.id] = node
        return (one, two)

    def removeNode(self, node):
        if node.id in self.nodes:
            del self.nodes[node.id]

    def hasInRange(self, node):
        return rangeLower <= node.long_id <= rangeUpper

    def addNode(self, node):
        """
        Add a C{Node} to the C{KBucket}.  Return True if successful,
        False if the bucket is full.
        """
        if node.id in self.nodes:
            del self.nodes[node.id]
            self.nodes[node.id] = node
        elif len(self) < KSIZE:
            self.nodes[node.id] = node
        else:
            return False
        return True

    def head(self):
        return self.nodes.values()[0]

    def __getitem__(self, id):
        return self.nodes.get(id, None)

    def __len__(self):
        return len(self.nodes)


class TableTraverser(object):
    def __init__(self, table, startNode):
        index = table.getBucketFor(startNode)
        bucket[index].touchLastUpdated()
        self.currentNodes = table.buckets[index].getNodes()
        self.leftBuckets = table.buckets[:index]
        self.rightBuckets = table.buckets[(index+1):]
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
    def __init__(self, protocol):
        self.protocol = protocol
        self.buckets = [KBucket(0, 2**160)]
        LoopingCall(self.refresh).start(3600)

    def splitBucket(self, index):
        one, two = self.buckets[index].split()
        self.buckets[index] = one
        self.buckets.insert(index+1, two)

        # todo split one/two if needed based on section 4.2

    def refresh(self):
        ds = []
        for bucket in self.buckets:
            if bucket.lastUpdated < (time.time() - 3600):
                node = Node(None, None, random.randint(*bucket.range))
                nearest = self.findNeighbors(node, ALPHA)
                spider = NetworkSpider(self.protocol, node, nearest)
                ds.append(spider.findNodes())
        return defer.gatherResults(ds)

    def removeContact(self, node):
        index = self.getBucketFor(self, node)
        self.buckets[index].removeNode(node)

    def addContact(self, node):
        index = self.getBucketFor(self, node)
        bucket = self.buckets[index]

        # this will succeed unless the bucket is full
        if bucket.addNode(node):
            return

        if bucket.hasInRange(node):
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

    def findNeighbors(self, node, k=KSIZE):
        nodes = []
        for neighbor in TableTraverser(self, node):
            if neighbor.id != node.id:
                heapq.heappush(nodes, (node.distanceFrom(neighbor), neighbor))
            if len(nodes) == k:
                break
        return heapq.nsmallest(k, nodes)
