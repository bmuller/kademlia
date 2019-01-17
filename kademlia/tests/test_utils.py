import hashlib
import unittest

from kademlia.utils import digest, shared_prefix


class UtilsTest(unittest.TestCase):
    def test_digest(self):
        dig = hashlib.sha1(b'1').digest()
        self.assertEqual(dig, digest(1))

        dig = hashlib.sha1(b'another').digest()
        self.assertEqual(dig, digest('another'))

    def test_shared_prefix(self):
        args = ['prefix', 'prefixasdf', 'prefix', 'prefixxxx']
        self.assertEqual(shared_prefix(args), 'prefix')

        args = ['p', 'prefixasdf', 'prefix', 'prefixxxx']
        self.assertEqual(shared_prefix(args), 'p')

        args = ['one', 'two']
        self.assertEqual(shared_prefix(args), '')

        args = ['hi']
        self.assertEqual(shared_prefix(args), 'hi')
