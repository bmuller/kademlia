"""
General catchall for functions that don't make sense as methods.
"""
import hashlib
import operator

from twisted.internet import defer


def digest(s):
    if not isinstance(s, str):
        s = str(s)
    return hashlib.sha1(s).digest()


def deferredDict(d):
    """
    Just like a C{defer.DeferredList} but instead accepts and returns a C{dict}.

    @param d: A C{dict} whose values are all C{Deferred} objects.

    @return: A C{DeferredList} whose callback will be given a dictionary whose
    keys are the same as the parameter C{d}'s and whose values are the results
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
    def push(self, thing):
        if thing in self:
            self.remove(thing)
        self.append(thing)


def sharedPrefix(args):
    """
    Find the shared prefix between the strings.

    For instance, sharedPrefix(['blahblah', 'blahwhat']) is
    'blah'.
    """
    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1
    return args[0][:i]
