import time
from itertools import izip
from itertools import imap
from itertools import takewhile
import operator
from collections import OrderedDict


class ForgetfulStorage(object):
    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl

    def __setitem__(self, key, value):
        if key in self.data:
            del self.data[key]
        self.data[key] = (time.time(), value)
        self.cull()

    def cull(self):
        for k, v in self.iteritemsOlderThan(self.ttl):
            self.data.popitem(first=True)

    def get(self, key, default=None):
        self.cull()
        if key in self.data:
            return self[key]
        return default

    def __getitem__(self, key):
        self.cull()
        return self.data[key][1]

    def __iter__(self):
        self.cull()
        return iter(self.data)

    def __repr__(self):
        self.cull()
        return repr(self.data)

    def iteritemsOlderThan(self, secondsOld):
        minBirthday = time.time() - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return imap(operator.itemgetter(0, 2), matches)

    def _tripleIterable(self):
        ikeys = self.data.iterkeys()
        ibirthday = imap(operator.itemgetter(0), self.data.itervalues())
        ivalues = imap(operator.itemgetter(1), self.data.itervalues())
        return izip(ikeys, ibirthday, ivalues)

    def iteritems(self):
        self.cull()
        ikeys = self.data.iterkeys()
        ivalues = imap(operator.itemgetter(1), self.data.itervalues())
        return izip(ikeys, ivalues)
