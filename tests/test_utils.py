import hashlib

from kademlia.utils import *


class TestUtils:
    def test_digest(self): 
        dig = hashlib.sha1(b'1').digest()
        assert dig == digest(1)

        dig = hashlib.sha1(b'another').digest()
        assert dig == digest('another')

    def test_shared_prefix(self):  
        args = ['prefix', 'prefixasdf', 'prefix', 'prefixxxx']
        assert shared_prefix(args) == 'prefix'

        args = ['p', 'prefixasdf', 'prefix', 'prefixxxx']
        assert shared_prefix(args) == 'p'

        args = ['one', 'two']
        assert shared_prefix(args) == ''

        args = ['hi']
        assert shared_prefix(args) == 'hi'

    def test_to_base16_int(self):
        n = 5
        n_as_bytes = bytes([n])
        assert hex_to_base_int(n_as_bytes.hex()) == n
