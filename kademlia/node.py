class Node:
    def __init__(self, ip, port, id=None):
        self.ip = ip
        self.port = port        
        self.id = id
        if id is not None:
            self.long_id = long(id.encode('hex'), 16)

    def distnaceTo(self, node):
        return self.long_id ^ node.long_id

    def __iter__(self):
        """
        Enables use of Node as a tuple - i.e., tuple(node) works.
        """
        return iter([self.ip, self.port, self.id])
