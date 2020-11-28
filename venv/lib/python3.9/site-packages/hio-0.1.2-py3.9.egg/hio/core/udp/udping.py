# -*- encoding: utf-8 -*-
"""
hio.core.udping Module
"""
import sys
import os
import errno
import socket

from binascii import hexlify


UDP_MAX_DATAGRAM_SIZE = (2 ** 16) - 1  # 65535
UDP_MAX_SAFE_PAYLOAD = 548  # IPV4 MTU 576 - udp headers 28
# IPV6 MTU is 1280 but headers are bigger
UDP_MAX_PACKET_SIZE = min(1024, UDP_MAX_DATAGRAM_SIZE)  # assumes IPV6 capable equipment


class SocketUdpNb(object):
    """
    Class to manage non blocking I/O on UDP socket.
    """

    def __init__(self,
                 ha=None,
                 host='',
                 port=55000,
                 bufsize=1024,
                 wlog=None,
                 bcast=False):
        """
        Initialization method for instance.

        ha = host address duple (host, port)
        host = '' equivalant to any interface on host
        port = socket port
        bs = buffer size
        path = path to log file directory
        wlog = WireLog reference for debug logging or over the wire tx and rx
        bcast = Flag if True enables sending to broadcast addresses on socket
        """
        self.ha = ha or (host, port)  # ha = host address duple (host, port)
        self.bs = bufsize
        self.wlog = wlog
        self.bcast = bcast

        self.ss = None #server's socket needs to be opened
        self.opened = False

    def actualBufSizes(self):
        """
        Returns duple of the the actual socket send and receive buffer size
        (send, receive)
        """
        if not self.ss:
            return (0, 0)

        return (self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
                self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))

    def open(self):
        """
        Opens socket in non blocking mode.

        if socket not closed properly, binding socket gets error
           socket.error: (48, 'Address already in use')
        """
        #create socket ss = server socket
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if self.bcast:  # enable sending to broadcast addresses
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # make socket address reusable. doesn't seem to have an effect.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        # may want to look at SO_REUSEPORT
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) <  self.bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < self.bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)
        self.ss.setblocking(0) #non blocking socket

        #bind to Host Address Port
        try:
            self.ss.bind(self.ha)
        except socket.error as ex:
            console.terse("socket.error = {0}\n".format(ex))
            return False

        self.ha = self.ss.getsockname() #get resolved ha after bind
        self.opened = True
        return True

    def reopen(self):
        """
        Idempotently open socket
        """
        self.close()
        return self.open()

    def close(self):
        """
        Closes  socket and logs if any
        """
        if self.ss:
            self.ss.close() #close socket
            self.ss = None
            self.opened = False

    def receive(self):
        """
        Perform non blocking read on  socket.

        returns tuple of form (data, sa)
        if no data then returns (b'',None)
        but always returns a tuple with two elements
        """
        try:
            data, sa = self.ss.recvfrom(self.bs)  # sa is source (host, port)
        except socket.error as ex:
            # ex.args[0] is always ex.errno for better compat
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                return (b'', None) #receive has nothing empty string for data
            else:
                emsg = "socket.error = {0}: receiving at {1}\n".format(ex, self.ha)
                console.profuse(emsg)
                raise #re raise exception ex1

        if console._verbosity >= console.Wordage.profuse:  # faster to check
            try:
                load = data.decode("UTF-8")
            except UnicodeDecodeError as ex:
                load = "0x{0}".format(hexlify(data).decode("ASCII"))
            cmsg = ("Server at {0}, received from {1}:\n------------\n"
                       "{2}\n\n".format(self.ha, sa, load))
            console.profuse(cmsg)

        if self.wlog:  # log over the wire rx
            self.wlog.writeRx(sa, data)

        return (data, sa)

    def send(self, data, da):
        """
        Perform non blocking send on  socket.

        data is string in python2 and bytes in python3
        da is destination address tuple (destHost, destPort)
        """
        try:
            result = self.ss.sendto(data, da) #result is number of bytes sent
        except socket.error as ex:
            emsg = "socket.error = {0}: sending from {1} to {2}\n".format(ex, self.ha, da)
            console.profuse(emsg)
            result = 0
            raise

        if console._verbosity >=  console.Wordage.profuse:
            try:
                load = data[:result].decode("UTF-8")
            except UnicodeDecodeError as ex:
                load = "0x{0}".format(hexlify(data[:result]).decode("ASCII"))
            cmsg = ("Server at {0}, sent {1} bytes to {2}:\n------------\n"
                    "{3}\n\n".format(self.ha, result, da, load))
            console.profuse(cmsg)

        if self.wlog:
            self.wlog.writeTx(da, data[:result])

        return result


PeerUdp = SocketUdpNb  # alias
