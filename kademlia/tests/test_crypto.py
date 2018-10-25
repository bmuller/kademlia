import unittest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from unittest.mock import Mock, ANY

from kademlia.crypto import Crypto
from kademlia.dto.dto import PublicKey


class CryptoTests(unittest.TestCase):

    def setUp(self):
        self.crypto = Crypto()

    def test_get_signature(self):
        """
        get_signature should return signature for specified value and private key
        """
        mocked_pk = Mock()
        mocked_pk.sign = Mock(return_value='test signature')
        serialization.load_pem_private_key = Mock(return_value=mocked_pk)

        value = 'test value'.encode('utf8')

        signature = self.crypto.get_signature(value, 'private key')
        self.assertEqual(signature, 'test signature')
        serialization.load_pem_private_key.assert_called_with('private key', password=None, backend=default_backend())
        mocked_pk.sign.assert_called_with(b'47d1d8273710fd6f6a5995fac1a0983fe0e8828c288e35e80450ddc5c4412def', ANY, ANY)
        self.crypto.get_signature(value, 'private key', 'password')
        serialization.load_pem_private_key.assert_called_with('private key', password='password', backend=default_backend())

    def test_check_signature(self):
        """
        check_signature should validate signature
        """
        mocked_pk = Mock()
        mocked_pk.verify = Mock()
        serialization.load_pem_public_key = Mock(return_value=mocked_pk)

        public_key = 'dGVzdCBrZXk='
        signature = 'dGVzdCBzaWduYXR1cmU='
        value = 'test value'.encode('utf8')

        self.crypto.check_signature(value, signature, public_key)
        serialization.load_pem_public_key.assert_called_with(b'test key', backend=default_backend())
        mocked_pk.verify.assert_called_with(b'test signature', b'47d1d8273710fd6f6a5995fac1a0983fe0e8828c288e35e80450ddc5c4412def', ANY, ANY)


class PublicKeyTests(unittest.TestCase):

    def test__init__(self):
        """
        __init__ should set initial values for key and exp_time
        """
        public_key = PublicKey('test key')
        self.assertEqual(public_key.key, 'test key')
        self.assertIsNone(public_key.exp_time)
        public_key = PublicKey('test key', 123)
        self.assertEqual(public_key.exp_time, 123)

    def test_key_set(self):
        """
        key.set should check type and set key
        """
        public_key = PublicKey('test key')
        public_key.key = 'another key'
        self.assertEqual(public_key.key, 'another key')
        public_key.key = None
        self.assertEqual(public_key.key, None)
        with self.assertRaises(AssertionError):
           public_key.key = 123

    def test_of_json(self):
        """
        of_json should set key and exp_time from json
        """
        json = dict()
        json2 = dict()
        json['key'] = 'test key'
        json['exp_time'] = 123
        public_key = PublicKey.of_json(json)
        self.assertEqual(public_key.key, 'test key')
        self.assertEqual(public_key.exp_time, 123)
        with self.assertRaises(AssertionError):
            public_key = PublicKey.of_json(json2)