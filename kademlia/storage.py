import time
import json
import operator
from itertools import takewhile
from collections import OrderedDict

DATA_PATH = 'data/'
KEYS_STORE = 'keys.json'


class IStorage:
    def __init__(self):
        self.i = 0
        self.keys = OrderedDict()
        self.initKeys()

    def __setitem__(self, key, value):
        if key in self.keys:
            del self.keys[key]
        self.keys[key] = int(time.time())
        with open(KEYS_STORE, 'w') as outfile:
            json.dump(self.convertKeysToHex(self.keys), outfile)
        with open(DATA_PATH + key.hex() + '.json', 'w') as outfile:
            json.dump(value, outfile)

    def get(self, key, default=None):
        if key in self.keys:
            return self.readKeyFromJSON(key)
        return default

    def __getitem__(self, key):
        return self.readKeyFromJSON(key)

    def readKeyFromJSON(self, key):
        with open(DATA_PATH + key.hex() + '.json') as json_file:
            return json.load(json_file)

    def __iter__(self):
        return self

    def next(self):
        if self.i < len(self.keys):
            self.i += 1
            return self.keys.items()[self.i - 1]
        else:
            raise StopIteration()

    def __repr__(self):
        return repr(self.keys)

    def iteritemsOlderThan(self, secondsOld):
        minBirthday = int(time.time()) - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _tripleIterable(self):
        ikeys = self.keys.keys()
        ibirthday = self.keys.values()
        ivalues = map(lambda k: self.get(k), self.keys.keys())
        return zip(ikeys, ibirthday, ivalues)

    def items(self):
        ikeys = self.keys.keys()
        ivalues = map(lambda k: self.get(k), self.keys.keys())
        return zip(ikeys, ivalues)

    def convertKeysToHex(self, data):
        result = OrderedDict()
        for key in data:
            result[key.hex()] = data[key]
        return result

    def initKeys(self):
        try:
            with open(KEYS_STORE) as json_file:
                try:
                    data = json.load(json_file)
                    for key in data:
                        self.keys[bytes.fromhex(key)] = data[key]
                except ValueError:
                    self.createEmptyKeysJSON()
        except FileNotFoundError:
            self.createEmptyKeysJSON()

    def createEmptyKeysJSON(self):
        with open(KEYS_STORE, 'w') as outfile:
            outfile.write("{}")


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
