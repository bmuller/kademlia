"""
General catchall for functions that don't make sense as methods.
"""
import hashlib
import logging
import operator
import asyncio
import time

from kademlia.crypto import Crypto
from kademlia.dto.dto import Value
from kademlia.exceptions import InvalidSignException, UnauthorizedOperationException

log = logging.getLogger(__name__)


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


def validate_authorization(dkey, value: Value):
    log.debug(f"Going to validate authorization for key {dkey.hex()}")
    sign = value.authorization.sign
    exp_time = value.authorization.pub_key.exp_time
    data = value.data
    assert exp_time is None or exp_time > int(time.time())

    dRecord = digest(str(dkey) + str(data) + str(exp_time))

    if not Crypto.check_signature(dRecord, sign, value.authorization.pub_key.key):
        raise InvalidSignException(sign)


def check_new_value_valid(dkey, stored_value: Value, new_value: Value):

    if stored_value.authorization is None and new_value.authorization is None:
        return True
    elif stored_value.authorization is None and new_value.authorization is not None:
        validate_authorization(dkey, new_value)
        return True
    elif stored_value.authorization is not None and new_value.authorization is not None:
        validate_authorization(dkey, new_value)
        if stored_value.authorization.pub_key.key == new_value.authorization.pub_key.key:
            return True
        else:
            raise UnauthorizedOperationException
    else:
        raise UnauthorizedOperationException
