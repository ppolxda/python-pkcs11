"""
Types for high level PKCS#11 wrapper.

This module provides stubs that are overrideen in pkcs11._pkcs11.
"""

from .constants import *
from .mechanisms import *


def _CK_UTF8CHAR_to_str(data):
    """Convert CK_UTF8CHAR to string."""
    # FIXME: the last couple of bytes are sometimes bogus, is this me
    # or SoftHSM?
    return data[:31].decode('utf-8').rstrip()


def _CK_VERSION_to_tuple(data):
    """Convert CK_VERSION to tuple."""
    return (data['major'], data['minor'])


class Slot:
    """
    A PKCS#11 device slot.

    This object represents a physical or software slot exposed by PKCS#11.
    A slot has hardware capabilities, e.g. supported mechanisms and may has
    a physical or software :class:`Token` installed.
    """

    def __init__(self, lib, slot_id,
                 slotDescription=None,
                 manufacturerID=None,
                 hardwareVersion=None,
                 firmwareVersion=None,
                 flags=None,
                 **kwargs):

        self._lib = lib  # Hold a reference to the lib to prevent gc

        self.slot_id = slot_id
        """Slot identifier (opaque)."""
        self.slot_description = _CK_UTF8CHAR_to_str(slotDescription)
        """Slot name (:class:`str`)."""
        self.manufacturer_id = _CK_UTF8CHAR_to_str(manufacturerID)
        """Slot/device manufacturer's name (:class:`str`)."""
        self.hardware_version = _CK_VERSION_to_tuple(hardwareVersion)
        """Hardware version (:class:`tuple`)."""
        self.firmware_version = _CK_VERSION_to_tuple(firmwareVersion)
        """Firmware version (:class:`tuple`)."""
        self.flags = SlotFlag(flags)
        """Capabilities of this slot (:class:`SlotFlag`)."""

    def get_token(self):
        """
        Returns the token loaded into this slot.

        :rtype: Token
        """
        raise NotImplementedError()

    def get_mechanisms(self):
        """
        Returns the mechanisms supported by this device.

        :rtype: set(Mechanism)
        """
        raise NotImplementedError()

    def __str__(self):
        return '\n'.join((
            "Slot Description: %s" % self.slot_description,
            "Manufacturer ID: %s" % self.manufacturer_id,
            "Hardware Version: %s.%s" % self.hardware_version,
            "Firmware Version: %s.%s" % self.firmware_version,
            "Flags: %s" % self.flags,
        ))

    def __repr__(self):
        return '<{klass} (slotID={slot_id} flags={flags})>'.format(
            klass=type(self).__name__,
            slot_id=self.slot_id,
            flags=str(self.flags))


class Token:
    """
    A PKCS#11 token.

    A token can be physically installed in a :class:`Slot`, or a software
    token, depending on your PKCS#11 library.
    """

    def __init__(self, slot,
                 label=None, serial=None, flags=None,
                 **kwargs):

        self.slot = slot
        """The :class:`Slot` this token is installed in."""
        self.label = _CK_UTF8CHAR_to_str(label)
        """Label of this token (:class:`str`)."""
        self.serial = serial
        """Serial number of this token (:class:`bytes`)."""
        self.flags = TokenFlag(flags)
        """Capabilities of this token (:class:`TokenFlag`)."""

    def open(self, rw=False, user_pin=None, so_pin=None):
        """
        Open a session on the token.

        Can be used as a context manager.

        :rtype: Session
        """
        raise NotImplementedError()

    def __str__(self):
        return self.label

    def __repr__(self):
        return "<{klass} (label='{label}' serial={serial} flags={flags})>"\
            .format(klass=type(self).__name__,
                    label=self.label,
                    serial=self.serial,
                    flags=str(self.flags))


class Session:
    """
    A PKCS#11 :class:`Token` session.

    A session is required to do nearly all operations on a token including
    encryption/signing/keygen etc.

    Create a session using :meth:`Token.open`. Sessions can be used as a
    context manager or closed with :meth:`close`.
    """

    def __init__(self, token, handle, rw=False, user_type=UserType.NOBODY):
        self.token = token
        """:class:`Token` this session is on."""

        self._handle = handle
        self.rw = rw
        """True if this is a read/write session."""
        self.user_type = user_type
        """User type for this session (:class:`UserType`)."""

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def close(self):
        """Close the session."""
        raise NotImplementedError()

    def generate_key(self, key_type, key_length,
                     id=None, label=None,
                     store=True, capabilities=None,
                     mechanism=None, mechanism_param=b'',
                     template=None):
        """
        Generate a single key (e.g. AES, DES).

        Keys should set at least `id` or `label`.

        An appropriate `mechanism` will be chosen for `key_type`
        (see :attr:`DEFAULT_GENERATE_MECHANISMS`) or this can be overridden.
        Similarly the `capabilities` (see :attr:`DEFAULT_KEY_CAPABILITIES`).

        The `template` will extend the default template used to make the
        key.

        :param KeyType key_type: Key type (e.g. KeyType.AES)
        :param int key_length: Key length in bits (e.g. 256).
        :param bytes id: Key identifier.
        :param str label: Key label.
        :param store: Store key on token.
        :param MechanismFlag capabilities: Key capabilities (or default).
        :param Mechanism mechanism: Generation mechanism (or default).
        :param bytes mechanism_param: Optional vector to the mechanism.
        :param dict(Attribute, any) template: Additional attributes.

        :rtype: SymmetricKey
        """
        raise NotImplementedError()


class Object:
    """
    A PKCS#11 object residing on a :class:`Token`.

    Objects implement :meth:`__getitem__` and :meth:`__setitem__` to
    retrieve :class:`Attribute`s on the object.
    """

    object_class = None
    """:class:`ObjectClass` of this Object."""

    def __init__(self, session, handle):
        self.session = session
        """:class:`Session` this object is valid for."""
        self._handle = handle

    def destroy(self):
        """Destroy the object."""
        raise NotImplementedError()


class Key(Object):
    """Base class for all key objects."""

    @property
    def key_type(self):
        """Key type."""
        return self[Attribute.KEY_TYPE]


class SecretKey(Key):
    """
    A PKCS#11 :attr:`ObjectClass.SECRET_KEY` object (symmetric encryption key).
    """

    object_class = ObjectClass.SECRET_KEY



class EncryptMixin(Object):
    """
    This object supports the encrypt capability.
    """

    def _encrypt(self, data, mechanism=None, mechanism_param=b''):
        raise NotImplementedError()

    def encrypt(self, data, **kwargs):
        """Do an encryption operation."""

        # If data is a string, encode it now as UTF-8.
        if isinstance(data, str):
            data = data.encode('utf-8')

        # If we're not an iterable, recurse into ourselves with an iterable
        # version and join the result at the end.
        if isinstance(data, bytes):
            return b''.join(self._encrypt((data,), **kwargs))

        else:
            return self._encrypt(data, **kwargs)


class DecryptMixin(Object):
    pass


class SignMixin(Object):
    pass


class VerifyMixin(Object):
    pass


class WrapMixin(Object):
    pass


class UnwrapMixin(Object):
    pass
