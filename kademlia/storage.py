import time
from collections import OrderedDict

class ForgetfulStorage(object):
    def __init__(self, ttl=7200):
        """
        By default, max age is 2 hours
        """
        self.data = OrderedDict()
        self.ttl = ttl

    def __setitem__(self, key, value):
        if key in self.data:
            del self.data[key]
        self.data[key] = (time.time() + self.ttl, value)
        self.cull()

    def cull(self):
        pop = 0
        for value in self.data.itervalues():
            if value[0] >= time.time():
                break
            pop += 1
        for _ in xrange(pop):
            self.data.popitem(first=True)

    def __getitem__(self, key):
        self.cull()
        return self.data[key][1]

    def __iter__(self):
        self.cull()
        return iter(self.data)

    def __repr__(self):
        self.cull()
        return repr(self.data)
