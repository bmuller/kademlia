import logging

import hashlib
import base64

from kademlia.helpers import JsonSerializable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

log = logging.getLogger(__name__)


class Crypto(object):

    @staticmethod
    def get_signature(value, priv_key, password=None):

        privkey = serialization.load_pem_private_key(
            priv_key, password=password, backend=default_backend())

        prehashed = bytes(hashlib.sha256(value).hexdigest(), 'ascii')

        sig = privkey.sign(
            prehashed,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256())

        return sig

    @staticmethod
    def check_signature(value, signature, pub_key):

        decoded_key = base64.b64decode(pub_key)
        serialized_key = serialization.load_ssh_public_key(decoded_key, backend=default_backend())
        decoded_sig = base64.b64decode(signature)

        prehashed_val = bytes(hashlib.sha256(value).hexdigest(), 'ascii')

        try:
            serialized_key.verify(
                decoded_sig,
                prehashed_val,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())
            return True
        except InvalidSignature:
            return False


class PrivateKey(object):

    def __init__(self, path_to_priv_key, pass_phrase=None):
        self.key = open(path_to_priv_key).read().encode('ascii')
        self.passPhrase = pass_phrase

    def sign(self, value):

        privkey = serialization.load_pem_private_key(
            self.key, password=self.passPhrase, backend=default_backend())

        prehashed = bytes(hashlib.sha256(value).hexdigest(), 'ascii')

        signature = privkey.sign(
            prehashed,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256())

        return signature


class PublicKey(JsonSerializable):

    def __init__(self, base64_pub_key, exp_time=None):
        self.key = base64_pub_key
        self.exp_time = exp_time

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, base64_pub_key):
        check_pkey_type(base64_pub_key)
        self._key = base64_pub_key

    @property
    def exp_time(self):
        return self._exp_time

    @exp_time.setter
    def exp_time(self, exp_time):
        self._exp_time = exp_time

    @staticmethod
    def of_json(dct):
        assert 'exp_time' in dct
        assert 'key' in dct

        return PublicKey(dct['key'], dct['exp_time'])


def check_pkey_type(base64_pub_key):
    assert type(base64_pub_key) is str or base64_pub_key is None
