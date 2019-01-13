import time
from itertools import takewhile
import operator
from collections import OrderedDict
from abc import abstractmethod, ABC
import os
import shelve
from contextlib import closing, contextmanager
from threading import Lock

from _gdbm import error as shelve_error

from kademlia.utils import retry


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


class DiskStorage(IStorage):
    def __init__(self, filename=None):
        self.filename = os.path.realpath('kademlia.db')
        if filename:
            self.filename = os.path.realpath(filename)
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        self.lock = Lock()

    # pylint: disable=no-self-use
    def _key(self, key):
        if isinstance(key, bytes):
            return key.hex()
        return key

    @contextmanager
    def database(self):
        with self.lock:
            with closing(shelve.open(self.filename)) as database:
                yield database

    @retry(shelve_error)
    def __setitem__(self, key, item):
        with self.database() as database:
            # pylint: disable=unsupported-assignment-operation
            database[self._key(key)] = (time.monotonic(), item)

    @retry(shelve_error)
    def __getitem__(self, key):
        with self.database() as database:
            # pylint: disable=unsubscriptable-object
            result = database[self._key(key)][1]
        return result

    @retry(shelve_error)
    def get(self, key, default=None):
        with self.database() as database:
            result = default
            # pylint: disable=unsupported-membership-test
            if self._key(key) in database:
                # pylint: disable=unsubscriptable-object
                result = database[self._key(key)][1]
        return result

    @retry(shelve_error)
    def __delitem__(self, key):
        with self.database() as database:
            # pylint: disable=unsupported-delete-operation
            del database[self._key(key)]

    @retry(shelve_error)
    def __contains__(self, item):
        with self.database() as database:
            # pylint: disable=unsupported-membership-test
            result = item in database
        return result

    @retry(shelve_error)
    def __iter__(self):
        with self.database() as database:
            # pylint: disable=no-member
            for k in database.keys():
                # pylint: disable=unsubscriptable-object
                yield (k, database[k][1])

    @retry(shelve_error)
    def iter_older_than(self, seconds_old):
        with self.database() as database:
            min_birthday = time.monotonic() - seconds_old
            zipped = self._triple_iter(database)
            matches = takewhile(lambda r: min_birthday >= r[1], zipped)
            result = list(map(operator.itemgetter(0, 2), matches))
        return result

    def _triple_iter(self, database):
        ikeys = list(database.keys())
        ibirthday = map(operator.itemgetter(0), database.values())
        ivalues = map(operator.itemgetter(1), database.values())
        return zip(ikeys, ibirthday, ivalues)
