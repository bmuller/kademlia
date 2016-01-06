from __future__ import unicode_literals

import time

try:
    import itertools.izip as zip  # py2
except ImportError:
    pass

try:
    import itertools.imap as map  # py2
except ImportError:
    pass

from itertools import takewhile
import operator
from collections import OrderedDict

from zope.interface import implementer
from zope.interface import Interface


class IStorage(Interface):
    """
    Local storage for this node.
    """

    def __setitem__(key, value):
        """
        Set a key to the given value.
        """

    def __getitem__(key):
        """
        Get the given key.  If item doesn't exist, raises C{KeyError}
        """

    def get(key, default=None):
        """
        Get given key.  If not found, return default.
        """

    def iteritemsOlderThan(secondsOld):
        """
        Return the an iterator over (key, value) tuples for items older than the given secondsOld.
        """

    def iteritems():
        """
        Get the iterator for this storage, should yield tuple of (key, value)
        """


@implementer(IStorage)
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
            self.data.popitem(last=False)

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
        return map(operator.itemgetter(0, 2), matches)

    def _tripleIterable(self):
        ikeys = iter(self.data.keys())
        ibirthday = map(operator.itemgetter(0), iter(self.data.values()))
        ivalues = map(operator.itemgetter(1), iter(self.data.values()))
        return zip(ikeys, ibirthday, ivalues)

    def iteritems(self):
        self.cull()
        ikeys = iter(self.data.keys())
        ivalues = map(operator.itemgetter(1), iter(self.data.values()))
        return zip(ikeys, ivalues)
