"""
Package for interacting on the network via a Async Protocol
"""
import asyncio
import logging
import os
from base64 import b64encode
from hashlib import sha1

import umsgpack

from rpcudp.exceptions import MalformedMessage

LOG = logging.getLogger(__name__)


class RPCProtocol(asyncio.DatagramProtocol):
    """
    Protocol implementation using msgpack to encode messages and asyncio
    to handle async sending / recieving.
    """
    def __init__(self, wait_timeout=5):
        """
        Create a protocol instance.

        Args:
            wait_timeout (int): Time to wait for a response before giving up
        """
        self._wait_timeout = wait_timeout
        self._outstanding = {}
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        LOG.debug("received datagram from %s", addr)
        asyncio.ensure_future(self._solve_datagram(data, addr))

    async def _solve_datagram(self, datagram, address):
        if len(datagram) < 22:
            LOG.warning("received datagram too small from %s,"
                        " ignoring", address)
            return

        msg_id = datagram[1:21]
        data = umsgpack.unpackb(datagram[21:])

        if datagram[:1] == b'\x00':
            # schedule accepting request and returning the result
            asyncio.ensure_future(self._accept_request(msg_id, data, address))
        elif datagram[:1] == b'\x01':
            self._accept_response(msg_id, data, address)
        else:
            # otherwise, don't know the format, don't do anything
            LOG.debug("Received unknown message from %s, ignoring", address)

    def _accept_response(self, msg_id, data, address):
        msgargs = (b64encode(msg_id), address)
        if msg_id not in self._outstanding:
            LOG.warning("received unknown message %s "
                        "from %s; ignoring", *msgargs)
            return
        LOG.debug("received response %s for message "
                  "id %s from %s", data, *msgargs)
        future, timeout = self._outstanding[msg_id]
        timeout.cancel()
        future.set_result((True, data))
        del self._outstanding[msg_id]

    async def _accept_request(self, msg_id, data, address):
        if not isinstance(data, list) or len(data) != 2:
            raise MalformedMessage("Could not read packet: %s" % data)
        funcname, args = data
        func = getattr(self, "rpc_%s" % funcname, None)
        if func is None or not callable(func):
            msgargs = (self.__class__.__name__, funcname)
            LOG.warning("%s has no callable method "
                        "rpc_%s; ignoring request", *msgargs)
            return

        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        response = await func(address, *args)
        LOG.debug("sending response %s for msg id %s to %s",
                  response, b64encode(msg_id), address)
        txdata = b'\x01' + msg_id + umsgpack.packb(response)
        self.transport.sendto(txdata, address)

    def _timeout(self, msg_id):
        args = (b64encode(msg_id), self._wait_timeout)
        LOG.error("Did not receive reply for msg "
                  "id %s within %i seconds", *args)
        self._outstanding[msg_id][0].set_result((False, None))
        del self._outstanding[msg_id]

    def __getattr__(self, name):
        """
        If name begins with "_" or "rpc_", returns the value of
        the attribute in question as normal.

        Otherwise, returns the value as normal *if* the attribute
        exists, but does *not* raise AttributeError if it doesn't.

        Instead, returns a closure, func, which takes an argument
        "address" and additional arbitrary args (but not kwargs).

        func attempts to call a remote method "rpc_{name}",
        passing those args, on a node reachable at address.
        """
        if name.startswith("_") or name.startswith("rpc_"):
            return getattr(super(), name)

        try:
            return getattr(super(), name)
        except AttributeError:
            pass

        def func(address, *args):
            msg_id = sha1(os.urandom(32)).digest()
            data = umsgpack.packb([name, args])
            if len(data) > 8192:
                raise MalformedMessage("Total length of function "
                                       "name and arguments cannot exceed 8K")
            txdata = b'\x00' + msg_id + data
            LOG.debug("calling remote function %s on %s (msgid %s)",
                      name, address, b64encode(msg_id))
            self.transport.sendto(txdata, address)

            loop = asyncio.get_event_loop()
            if hasattr(loop, 'create_future'):
                future = loop.create_future()
            else:
                future = asyncio.Future()
            timeout = loop.call_later(self._wait_timeout,
                                      self._timeout, msg_id)
            self._outstanding[msg_id] = (future, timeout)
            return future

        return func
