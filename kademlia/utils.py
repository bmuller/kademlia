"""
General catchall for functions that don't make sense as methods.
"""
import hashlib
import operator
import sys
import binascii

from twisted.internet import defer


# Converts unprintable strings to printable hex (if needed.)
def safe_log_var(v):
    try:
        v.encode("ascii")
        return v.decode("utf-8") + u" (ascii)"
    except UnicodeEncodeError:
        # To a byte string.
        as_bytes = b""
        if sys.version_info >= (3,0,0):
            codes = []
            for ch in v:
                codes.append(ord(ch))

            if len(codes):
                as_bytes = bytes(codes)
        else:
            for ch in v:
                as_bytes += chr(ord(ch))

        return binascii.hexlify(as_bytes).decode("utf-8") + u" (hex)"
    except UnicodeDecodeError:
        return binascii.hexlify(v).decode("utf-8") + u" (hex)"

        
def digest(s):
    if not isinstance(s, str):
        s = str(s)
    return hashlib.sha1(s).digest()


def deferredDict(d):
    """
    Just like a :class:`defer.DeferredList` but instead accepts and returns a :class:`dict`.

    Args:
        d: A :class:`dict` whose values are all :class:`defer.Deferred` objects.

    Returns:
        :class:`defer.DeferredList` whose callback will be given a dictionary whose
        keys are the same as the parameter :obj:`d` and whose values are the results
        of each individual deferred call.
    """
    if len(d) == 0:
        return defer.succeed({})

    def handle(results, names):
        rvalue = {}
        for index in range(len(results)):
            rvalue[names[index]] = results[index][1]
        return rvalue

    dl = defer.DeferredList(d.values())
    return dl.addCallback(handle, d.keys())


class OrderedSet(list):
    """
    Acts like a list in all ways, except in the behavior of the :meth:`push` method.
    """

    def push(self, thing):
        """
        1. If the item exists in the list, it's removed
        2. The item is pushed to the end of the list
        """
        if thing in self:
            self.remove(thing)
        self.append(thing)


def sharedPrefix(args):
    """
    Find the shared prefix between the strings.

    For instance:

        sharedPrefix(['blahblah', 'blahwhat'])

    returns 'blah'.
    """
    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1
    return args[0][:i]
