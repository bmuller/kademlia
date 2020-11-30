import time
from itertools import takewhile
import operator
from collections import OrderedDict
from abc import abstractmethod, ABC


class IStorage(ABC):
    """
    Local storage for this node.
    IStorage implementations of get must return the same type as put in by set
    """

    @abstractmethod
    def __setitem__(self, key, value):
        """
        Set a key to the given value.
        """

    @abstractmethod
    def __getitem__(self, key):
        """
        Get the given key.  If item doesn't exist, raises C{KeyError}
        """

    @abstractmethod
    def get(self, key, default=None):
        """
        Get given key.  If not found, return default.
        """

    @abstractmethod
    def iter_older_than(self, seconds_old):
        """
        Return the an iterator over (key, value) tuples for items older
        than the given secondsOld.
        """

    @abstractmethod
    def __iter__(self):
        """
        Get the iterator for this storage, should yield tuple of (key, value)
        """

class KeriStorage(IStorage):
    def __init__(self, baser, ttl=604800):
        self.baser = baser

        # TODO this belongs in Keri
        self.db_mappings = {
            b'evts.': self.baser.evts,
            b'dtss.': self.baser.dtss,
            b'sigs.': self.baser.sigs,
            b'rcts.': self.baser.rcts,
            b'ures.': self.baser.ures,
            b'vrcs.': self.baser.vrcs,
            b'vres.': self.baser.vres,
            b'kels.': self.baser.kels,
            b'pses.': self.baser.pses,
            b'ooes.': self.baser.ooes,
            b'dels.': self.baser.dels,
            b'ldes.': self.baser.ldes
        }

    def __setitem__(self, key, value):
        """
        Set a key to the given value.
        """
        db = self._get_baser_db(key)

        if isinstance(value, str):
            self.baser.setVal(db, key, value.encode())
        else:
            self.baser.setVal(db, key, value)

    def __getitem__(self, key):
        """
        Get the given key.  If item doesn't exist, raises C{KeyError}
        """
        db = self._get_baser_db(key)
        value = self.baser.getVal(db, key)
        return bytes(value)

    def __repr__(self):
        return repr(self.baser)

    def get(self, key, default=None):
        """
        Get given key.  If not found, return default.
        """
        db = self._get_baser_db(key)
        value = self.baser.getVal(db, key)
        return default if value is None else bytes(value)

    def iter_older_than(self, seconds_old):
        """
        Return the an iterator over (key, value) tuples for items older
        than the given secondsOld.
        """
        raise NotImplementedError("will implement if necessary for keri")
        # TODO: if necessary, set time in all values and implement this
        # self.data[key] = (time.monotonic(), value)


    def __iter__(self):
        """
        Get the iterator for this storage, should yield tuple of (key, value)
        """

        # TODO: this only uses the evts database within Baser right now, but will need to look through
        # all dbs in the future. Determine how to look through ALL key-value pairs in ALL databases with an iterator
        # object to return here
        txn = self.baser.env.begin(db=self.db_mappings[b'evts.'], write=False, buffers=True)
        cursor = txn.cursor()
        return cursor.iternext(keys=True, values=True)

    def _get_baser_db(self, key):
        """
        Ensures the input key is a byte array of the form [database].[key], then returns each portion
        """
        if not isinstance(key, bytes):
            raise ValueError("key must be of type bytes")

        dbbytes = key[16:] + b'.'
        if len(dbbytes) != 5:
            raise ValueError(f"database name should only be 4 bytes but is {dbbytes}")

        if dbbytes not in self.db_mappings:
            raise ValueError(f"database name {dbbytes} is not a valid database")

        return self.db_mappings[dbbytes]


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
        for _, _ in self.iter_older_than(self.ttl):
            self.data.popitem(last=False)

    def get(self, key, default=None):
        self.cull()
        if key in self.data:
            return self[key]
        return default

    def __getitem__(self, key):
        self.cull()
        return self.data[key][1]

    def __repr__(self):
        self.cull()
        return repr(self.data)

    def iter_older_than(self, seconds_old):
        min_birthday = time.monotonic() - seconds_old
        zipped = self._triple_iter()
        matches = takewhile(lambda r: min_birthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _triple_iter(self):
        ikeys = self.data.keys()
        ibirthday = map(operator.itemgetter(0), self.data.values())
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ibirthday, ivalues)

    def __iter__(self):
        self.cull()
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)
