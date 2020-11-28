# -*- encoding: utf-8 -*-
"""
keri.help.helping module

"""
import os
import shutil
import tempfile
import base64
import datetime

from collections.abc import Iterable, Sequence,  Mapping

import pysodium

from multidict import MultiDict  # base class for mdict defined below
from orderedset import OrderedSet as oset


def keyToKey64u(key):
    """
    Returns 64u
    Convert and return bytes key to unicode base64 url-file safe version
    """
    return base64.urlsafe_b64encode(key).decode("utf-8")


def key64uToKey(key64u):
    """
    Returns bytes
    Convert and return unicode base64 url-file safe key64u to bytes key
    """
    return base64.urlsafe_b64decode(key64u.encode("utf-8"))


def verifyEd25519(sig, msg, vk):
    """
    Returns True if signature sig of message msg is verified with
    verification key vk Otherwise False
    All of sig, msg, vk are bytes
    """
    try:
        result = pysodium.crypto_sign_verify_detached(sig, msg, vk)
    except Exception as ex:
        return False
    return (True if result else False)


def verify64uEd25519(signature, message, verkey):
    """
    Returns True if signature is valid for message with respect to verification
    key verkey

    signature and verkey are encoded as unicode base64 url-file strings
    and message is unicode string as would be the case for a json object

    """
    sig = key64uToKey(signature)
    vk = key64uToKey(verkey)
    msg = message.encode("utf-8")
    return (verifyEd25519(sig, msg, vk))

class mdict(MultiDict):
    """
    Multiple valued dictionary. Insertion order of keys preserved.
    Associated with each key is a valuelist i.e. a list of values for that key.
    Extends  MultiDict
    https://multidict.readthedocs.io/en/stable/
    MultiDict keys must be subclass of str no ints allowed
    In MultiDict:
        .add(key,value)  appends value to the valuelist at key

        m["key"] = value replaces the valuelist at key with [value]

        m["key] treturns the first added element of the valuelist at key

    MultiDict methods access values in FIFO order
    mdict adds method to access values in LIFO order

    Extended methods in mdict but not in MultiDict are:
       nabone(key [,default])  get last value at key else default or KeyError
       nab(key [,default])  get last value at key else default or None
       naball(key [,default]) get all values inverse order else default or KeyError

    """

    def nabone(self, key, *pa, **kwa):
        """
        Usage:
            .nabone(key [, default])

        returns last value at key if key in dict else default
        raises KeyError if key not in dict and default not provided.
        """
        try:
            return self.getall(key)[-1]
        except KeyError:
            if not pa and "default" not in kwa:
                raise
            elif pa:
                return pa[0]
            else:
                return kwa["default"]


    def nab(self, key, *pa, **kwa):
        """
        Usage:
            .nab(key [, default])

        returns last value at key if key in dict else default
        returns None if key not in dict and default not provided.
        """
        try:
            return self.getall(key)[-1]
        except KeyError:
            if not pa and "default" not in kwa:
                return None
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def naball(self, key, *pa, **kwa):
        """
        Usage:
            .nabone(key [, default])

        returns list of value at key if key in dict else default
        raises KeyError if key not in dict and default not provided.
        """
        try:
            # getall returns copy of list so safe to reverse
            return list(reversed(self.getall(key)))
        except KeyError:
            if not pa and "default" not in kwa:
                raise
            elif pa:
                return pa[0]
            else:
                return kwa["default"]


    def firsts(self):
        """
        Returns list of (key, value) pair where each value is first value at key
        No duplicate keys

        This is useful for forked lists of values with same keys
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.getone(k)) for k in keys]


    def lasts(self):
        """
        Returns list of (key, value) pairs where each value is last value at key

        This is useful fo forked lists  of values with same keys
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.nabone(k)) for k in keys]


def nonStringIterable(obj):
    """
    Returns True if obj is non-string iterable, False otherwise

    Future proof way that is compatible with both Python3 and Python2 to check
    for non string iterables.

    Faster way that is less future proof
    return (hasattr(x, '__iter__') and not isinstance(x, (str, bytes)))
    """
    return (not isinstance(obj, (str, bytes)) and isinstance(obj, Iterable))

def nonStringSequence(obj):
    """
    Returns True if obj is non-string sequence, False otherwise

    Future proof way that is compatible with both Python3 and Python2 to check
    for non string sequences.

    """
    return (not isinstance(obj, (str, bytes)) and isinstance(obj, Sequence) )



def extractElementValues(element, values):
    """
    Recusive depth first search that recursively extracts value(s) from element
    and appends to values list

    Assumes that extracted values are str

    Parameters:
        element is some element to extract values from
        values is list of values from elements that are not nonStringIterables

    IF element is mapping or sequence (nonStringIterable) then
        recusively  extractValues from the items of that element

    Else
        append element to values list

    return

    """
    if nonStringIterable(element):
        if isinstance(element, Mapping):  # dict like
            for k in element:
                extractElementValues(element=element[k], values=values)
        else:
            for k in element:
                extractElementValues(element=k, values=values)

    elif isinstance(element, str):
        values.append(element)

    else:
        raise ValueError("Unexpected element value = {}. Not a str.".format(element))

    return

def extractValues(ked, labels):
    """
    Returns list of depth first recursively extracted values from elements of
    key event dict ked whose flabels are in lables list

    Parameters:
       ked is key event dict
       labels is list of element labels in ked from which to extract values
    """
    values = []
    for label in labels:
        extractElementValues(element=ked[label], values=values)

    return values


def nowIso8601():
    """
    Returns time now in ISO 8601 format
    use now(timezone.utc)

    YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM[:SS[.ffffff]]
    .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    '2020-08-22T17:50:09.988921+00:00'
    Assumes TZ aware
    For nanosecond use instead attotime or datatime64 in pandas or numpy
    """
    return (datetime.datetime.now(datetime.timezone.utc).isoformat())


def toIso8601(dt=None):
    """
    Returns str datetime dt in ISO 8601 format
    Converts datetime object dt to ISO 8601 formt
    If dt is missing use now(timezone.utc)

    YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM[:SS[.ffffff]]
    .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    '2020-08-22T17:50:09.988921+00:00'
    Assumes TZ aware
    For nanosecond use instead attotime or datatime64 in pandas or numpy
    """
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc)  # make it aware

    return(dt.isoformat())


def fromIso8601(dts):
    """
    Returns datetime object from ISO 8601 formated str
    Converts dts from ISO 8601 format to datetime object

    YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM[:SS[.ffffff]]
    .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    '2020-08-22T17:50:09.988921+00:00'
    Assumes TZ aware
    For nanosecond use instead attotime or datatime64 in pandas or numpy
    """
    return (datetime.datetime.fromisoformat(dts))
