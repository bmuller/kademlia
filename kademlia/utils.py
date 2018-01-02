"""
General catchall for functions that don't make sense as methods.
"""
import hashlib
import operator
import asyncio


async def gather_dict(d):
    cors = list(d.values())
    results = await asyncio.gather(*cors)
    return dict(zip(d.keys(), results))


def digest(s):
    if not isinstance(s, bytes):
        s = str(s).encode('utf8')
    return hashlib.sha1(s).digest()


class OrderedSet(list):
    """
    Acts like a list in all ways, except in the behavior of the
    :meth:`push` method.
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


def bytesToBitString(bites):
    bits = [bin(bite)[2:].rjust(8, '0') for bite in bites]
    return "".join(bits)
