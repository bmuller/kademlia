"""
General catchall for functions that don't make sense as methods.
"""
import hashlib
import operator
import asyncio
from functools import wraps
import time


async def gather_dict(dic):
    cors = list(dic.values())
    results = await asyncio.gather(*cors)
    return dict(zip(dic.keys(), results))


def digest(string):
    if not isinstance(string, bytes):
        string = str(string).encode('utf8')
    return hashlib.sha1(string).digest()


def shared_prefix(args):
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


def bytes_to_bit_string(bites):
    bits = [bin(bite)[2:].rjust(8, '0') for bite in bites]
    return "".join(bits)


def retry(exception_to_check, tries=4, delay=0.5, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    Args:
        exception_to_check (Exception): the exception to check.
                                        may be a tuple of exceptions to check
        tries (int): number of times to try (not retry) before giving up
        delay (float, int): initial delay between retries in seconds
        backoff (int): backoff multiplier e.g. value of 2 will double the delay
                       each retry
        logger (logging.Logger): logger to use. If None, print
    """
    def deco_retry(func):

        @wraps(func)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exception_to_check as exc:
                    msg = "%s, Retrying in %s seconds..." % (str(exc), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
