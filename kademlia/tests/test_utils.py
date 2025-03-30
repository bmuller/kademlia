import hashlib

from kademlia.utils import digest, shared_prefix


class TestUtils:
    def test_digest(self):
        dig = hashlib.sha1(b"1").digest()
        assert dig == digest(1)

        dig = hashlib.sha1(b"another").digest()
        assert dig == digest("another")

    def test_shared_prefix(self):
        args = ["prefix", "prefixasdf", "prefix", "prefixxxx"]
        assert shared_prefix(args) == "prefix"

        args = ["p", "prefixasdf", "prefix", "prefixxxx"]
        assert shared_prefix(args) == "p"

        args = ["one", "two"]
        assert shared_prefix(args) == ""

        args = ["hi"]
        assert shared_prefix(args) == "hi"
