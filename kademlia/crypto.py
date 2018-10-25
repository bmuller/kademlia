import logging

import hashlib
import base64

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
        serialized_key = serialization.load_pem_public_key(decoded_key, backend=default_backend())
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
