import hashlib
import unittest
from unittest.mock import Mock, patch
import time

from kademlia.crypto import Crypto
from kademlia.exceptions import InvalidSignException, UnauthorizedOperationException
from kademlia.utils import digest, sharedPrefix, OrderedSet, validate_authorization, check_new_value_valid


class UtilsTest(unittest.TestCase):
    def test_digest(self):
        d = hashlib.sha1(b'1').digest()
        self.assertEqual(d, digest(1))

        d = hashlib.sha1(b'another').digest()
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

    @patch('kademlia.utils.digest')
    @patch('time.time', Mock(return_value=5))
    def test_validate_authorization(self, mocked_digest):
        Crypto.check_signature = Mock(return_value=True)
        value = Mock()
        value.data = 'data'
        value.authorization.sign = 'sign'
        value.authorization.pub_key.exp_time = None
        value.authorization.pub_key.key = 'key'
        mocked_digest.return_value = 'digest'
        validate_authorization(hashlib.sha1('key'.encode('utf8')).digest(), value)
        Crypto.check_signature.assert_called_with('digest', 'sign', 'key')

        value.authorization.pub_key.exp_time = 6
        validate_authorization(hashlib.sha1('key'.encode('utf8')).digest(), value)
        Crypto.check_signature.assert_called_with('digest', 'sign', 'key')

        value.authorization.pub_key.exp_time = 4
        with self.assertRaises(AssertionError):
            validate_authorization(hashlib.sha1('key'.encode('utf8')).digest(), value)

        value.authorization.pub_key.exp_time = 6
        Crypto.check_signature = Mock(return_value=False)
        with self.assertRaises(InvalidSignException):
            validate_authorization(hashlib.sha1('key'.encode('utf8')).digest(), value)

    @patch('kademlia.utils.validate_authorization')
    def test_check_new_value_valid(self, mocked_va):
        stored_value = Mock()
        stored_value.authorization = None
        new_value = Mock()
        new_value.authorization = None
        self.assertTrue(check_new_value_valid('dkey', stored_value, new_value))

        new_value.authorization = 'authorization'
        self.assertTrue(check_new_value_valid('dkey', stored_value, new_value))
        mocked_va.assert_called_with('dkey', new_value)

        new_value.authorization = Mock()
        new_value.authorization.pub_key.key = 'key'
        stored_value.authorization = Mock()
        stored_value.authorization.pub_key.key = 'key'
        self.assertTrue(check_new_value_valid('dkey', stored_value, new_value))
        mocked_va.assert_called_with('dkey', new_value)

        new_value.authorization.pub_key.key = 'another key'
        with self.assertRaises(UnauthorizedOperationException):
            check_new_value_valid('dkey', stored_value, new_value)

        new_value.authorization = None
        with self.assertRaises(UnauthorizedOperationException):
            check_new_value_valid('dkey', stored_value, new_value)


class OrderedSetTest(unittest.TestCase):
    def test_order(self):
        o = OrderedSet()
        o.push('1')
        o.push('1')
        o.push('2')
        o.push('1')
        self.assertEqual(o, ['2', '1'])
