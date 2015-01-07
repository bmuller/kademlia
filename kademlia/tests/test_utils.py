import hashlib

from twisted.trial import unittest

from kademlia.utils import digest, sharedPrefix, OrderedSet


class UtilsTest(unittest.TestCase):
    def test_digest(self):
        d = hashlib.sha1('1').digest()
        self.assertEqual(d, digest(1))

        d = hashlib.sha1('another').digest()
        self.assertEqual(d, digest('another'))

    def test_sharedPrefix(self):
        args = ['prefix', 'prefixasdf', 'prefix', 'prefixxxx']
        self.assertEqual(sharedPrefix(args), 'prefix')

        args = ['p', 'prefixasdf', 'prefix', 'prefixxxx']
        self.assertEqual(sharedPrefix(args), 'p')

        args = ['one', 'two']
        self.assertEqual(sharedPrefix(args), '')

        args = ['hi']
        self.assertEqual(sharedPrefix(args), 'hi')


class OrderedSetTest(unittest.TestCase):
    def test_order(self):
        o = OrderedSet()
        o.push('1')
        o.push('1')
        o.push('2')
        o.push('1')
        self.assertEqual(o, ['2', '1'])
