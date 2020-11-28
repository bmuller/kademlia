import sys

__all__ = ["ReceiveBuffer"]


# Operations we want to support:
# - find next \r\n or \r\n\r\n, or wait until there is one
# - read at-most-N bytes
# Goals:
# - on average, do this fast
# - worst case, do this in O(n) where n is the number of bytes processed
# Plan:
# - store bytearray, offset, how far we've searched for a separator token
# - use the how-far-we've-searched data to avoid rescanning
# - while doing a stream of uninterrupted processing, advance offset instead
#   of constantly copying
# WARNING:
# - I haven't benchmarked or profiled any of this yet.
#
# Note that starting in Python 3.4, deleting the initial n bytes from a
# bytearray is amortized O(n), thanks to some excellent work by Antoine
# Martin:
#
#     https://bugs.python.org/issue19087
#
# This means that if we only supported 3.4+, we could get rid of the code here
# involving self._start and self.compress, because it's doing exactly the same
# thing that bytearray now does internally.
#
# BUT unfortunately, we still support 2.7, and reading short segments out of a
# long buffer MUST be O(bytes read) to avoid DoS issues, so we can't actually
# delete this code. Yet:
#
#     https://pythonclock.org/
#
# (Two things to double-check first though: make sure PyPy also has the
# optimization, and benchmark to make sure it's a win, since we do have a
# slightly clever thing where we delay calling compress() until we've
# processed a whole event, which could in theory be slightly more efficient
# than the internal bytearray support.)
class ReceiveBuffer(object):
    def __init__(self):
        self._data = bytearray()
        # These are both absolute offsets into self._data:
        self._start = 0
        self._looked_at = 0
        self._looked_for = b""

    def __bool__(self):
        return bool(len(self))

    # for @property unprocessed_data
    def __bytes__(self):
        return bytes(self._data[self._start :])

    if sys.version_info[0] < 3:  # version specific: Python 2
        __str__ = __bytes__
        __nonzero__ = __bool__

    def __len__(self):
        return len(self._data) - self._start

    def compress(self):
        # Heuristic: only compress if it lets us reduce size by a factor
        # of 2
        if self._start > len(self._data) // 2:
            del self._data[: self._start]
            self._looked_at -= self._start
            self._start -= self._start

    def __iadd__(self, byteslike):
        self._data += byteslike
        return self

    def maybe_extract_at_most(self, count):
        out = self._data[self._start : self._start + count]
        if not out:
            return None
        self._start += len(out)
        return out

    def maybe_extract_until_next(self, needle):
        # Returns extracted bytes on success (advancing offset), or None on
        # failure
        if self._looked_for == needle:
            search_start = max(self._start, self._looked_at - len(needle) + 1)
        else:
            search_start = self._start
        offset = self._data.find(needle, search_start)
        if offset == -1:
            self._looked_at = len(self._data)
            self._looked_for = needle
            return None
        new_start = offset + len(needle)
        out = self._data[self._start : new_start]
        self._start = new_start
        return out

    # HTTP/1.1 has a number of constructs where you keep reading lines until
    # you see a blank one. This does that, and then returns the lines.
    def maybe_extract_lines(self):
        if self._data[self._start : self._start + 2] == b"\r\n":
            self._start += 2
            return []
        else:
            data = self.maybe_extract_until_next(b"\r\n\r\n")
            if data is None:
                return None
            lines = data.split(b"\r\n")
            assert lines[-2] == lines[-1] == b""
            del lines[-2:]
            return lines
