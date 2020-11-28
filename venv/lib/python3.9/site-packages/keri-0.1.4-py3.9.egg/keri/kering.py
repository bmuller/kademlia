# -*- coding: utf-8 -*-
"""
Generic Constants and Classes
"""
import sys
from collections import namedtuple

Versionage = namedtuple("Versionage", "major minor")

Version = Versionage(major=1, minor=0)  # KERI Protocol Version

SEPARATOR =  "\r\n\r\n"
SEPARATOR_BYTES = SEPARATOR.encode("utf-8")


class KeriError(Exception):
    """
    Base Class for keri exceptions

    To use   raise KeriError("Error: message")
    """

class ShortageError(KeriError):
    """
    Not Enough bytes in buffer for complete message or material
    Usage:
        raise ShortageError("error message")
    """

class ValidationError(KeriError):
    """
    Validation related errors
    Usage:
        raise ValidationError("error message")
    """

class VersionError(ValidationError):
    """
    Bad or Unsupported Version

    Usage:
        raise VersionError("error message")
    """

class EmptyMaterialError(ValidationError):
    """
    Empty or Missing Crypto Material
    Usage:
        raise EmptyMaterialError("error message")
    """

class DerivationError(ValidationError):
    """
    Derivation related errors
    Usage:
        raise DerivationError("error message")
    """

