import time
import operator
import pickledb
from itertools import takewhile
from collections import OrderedDict


class IStorage:
    def __init__(self):
        self.data = pickledb.load('data.db', False)

    def __setitem__(self, key, value):
        self.data.set(key.hex(), (int(time.time()), value))
        self.data.dump()

    def get(self, key, default=None):
        value = self.data.get(key.hex())
        if value is not None:
            return value[1]
        return default

    def __getitem__(self, key):
        return self.data.get(key.hex())[1]

    def __iter__(self):
        return iter(self.items())

    def __repr__(self):
        return repr(self.data.getall())

    def iteritemsOlderThan(self, secondsOld):
        minBirthday = int(time.time()) - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _tripleIterable(self):
        ikeys = self.getAllKeysBytes()
        ibirthday = map(operator.itemgetter(0), self.getAllValues())
        ivalues = map(operator.itemgetter(1), self.getAllValues())
        return zip(ikeys, ibirthday, ivalues)

    def getAllValues(self):
        result = []
        for key in self.data.getall():
            result.append(self.data.get(key))
        return result

    def getAllKeysBytes(self):
        return list(map(lambda k: bytes.fromhex(k), self.data.getall()))

    def items(self):
        ikeys = self.getAllKeysBytes()
        ivalues = map(operator.itemgetter(1), self.getAllValues())
        return zip(ikeys, ivalues)


class ForgetfulStorage(IStorage):
    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl

    def __setitem__(self, key, value):
        if key in self.data:
            del self.data[key]
        self.data[key] = (time.monotonic(), value)
        self.cull()

    def cull(self):
        for _, _ in self.iteritemsOlderThan(self.ttl):
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
        minBirthday = time.monotonic() - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _tripleIterable(self):
        ikeys = self.data.keys()
        ibirthday = map(operator.itemgetter(0), self.data.values())
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ibirthday, ivalues)

    def items(self):
        self.cull()
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)
