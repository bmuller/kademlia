# -*- encoding: utf-8 -*-
"""
hio.core.tcp.serving Module

Accepter listens and accepts incoming TCP socket connections
Server is subclass of Acceptor
Server creates Incomers
Incomer is accepted incoming socket connection

ServerTls is subclass of Server
IncomerTls is subclass of Incomer

"""

import sys
import os
import errno
import socket
import ssl
from collections import deque
from binascii import hexlify

from contextlib import contextmanager

from ...base import tyming
from .. import coring


@contextmanager
def openServer(cls=None, **kwa):
    """
    Wrapper to create and open Server instances
    When used in with statement block, calls .close() on exit of with block

    Parameters:
        cls is Class instance of subclass instance

    Usage:
        with openServer() as server0:
            server0.

        with openServer(cls=ServerTls) as server0:
            server0.

    """
    cls = cls if cls is not None else Server

    try:
        server = cls(**kwa)
        server.reopen()  #  opens accept socket

        yield server

    finally:
        server.close()




class Acceptor(object):
    """
    Acceptor Base Class for Server.
    Nonblocking TCP Socket Acceptor Class.
    Listen socket for incoming TCP connections

    Attributes:
        .ha is (host,port) duple (two tuple)
               host = "" or "0.0.0.0" means listen on all interfaces
        .eha is normalized (host, port) duple for incoming TLS connections
                as external facing address for TLS context
        .bs is buffer size
        .ss is server listen socket for incoming accept requests
        .axes is deque of accepte connection duples (ca, cs)
        .opened is boolean, True if listen socket .ss opened. False otherwise
    """

    def __init__(self,
                 ha=None,
                 bs=8096,
                 ):
        """
        Initialization method for instance.
        ha is host address duple (host, port) listen interfaces
              host = "" or "0.0.0.0" means listen on all interfaces
        bs = buffer size

        """
        self.ha = ha or (host, port)  # ha = host address
        eha = self.ha
        host, port = eha  # expand so can normalize host
        host = coring.normalizeHost(host)
        if host in ('0.0.0.0',):
            host = '127.0.0.1'  # need specific interface for tls
        elif host in ("::", "0:0:0:0:0:0:0:0"):
            host = "::1" # need specific interface for tls
        self.eha = (host, port)
        self.bs = bs
        self.ss = None  # listen socket for accepts
        self.axes = deque()  # deque of duple (ca, cs) accepted connections
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
        Opens binds listen socket in non blocking mode.

        if socket not closed properly, binding socket gets error
           socket.error: (48, 'Address already in use')
        """
        #create server socket ss to listen on
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # make socket address reusable.
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in
        # TIME_WAIT state, without waiting for its natural timeout to expire.
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Linux TCP allocates twice the requested size
        if sys.platform.startswith('linux'):
            bs = 2 * self.bs  # get size is twice the set size
        else:
            bs = self.bs

        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) < bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.bs)
        if self.ss.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < bs:
            self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.bs)

        self.ss.setblocking(0) #non blocking socket

        try:  # bind to listen socket (host, port) to receive connections
            self.ss.bind(self.ha)
            self.ss.listen(5)
        except socket.error as ex:
            return False

        self.ha = self.ss.getsockname()  # get resolved ha after bind
        self.opened = True
        return True

    def reopen(self):
        """
        Idempotently opens listen socket
        """
        self.close()
        return self.open()

    def close(self):
        """
        Closes listen socket.
        """
        if self.ss:
            try:
                self.ss.shutdown(socket.SHUT_RDWR)  # shutdown socket
            except socket.error as ex:
                pass
            self.ss.close()  #close socket
            self.ss = None
            self.opened = False

    def accept(self):
        """
        Accept new connection nonblocking
        Returns duple (cs, ca) of connected socket and connected host address
        Otherwise if no new connection returns (None, None)
        """
        # accept new virtual connected socket created from server socket
        try:
            cs, ca = self.ss.accept()  # virtual connection (socket, host address)
        except socket.error as ex:
            if ex.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return (None, None)  # nothing yet
            raise  # re-raise

        return (cs, ca)

    def serviceAccepts(self):
        """
        Service any accept requests
        Adds to .cxes dict key by ca
        """
        while True:
            cs, ca = self.accept()
            if not cs:
                break
            self.axes.append((cs, ca))


class Server(Acceptor):
    """
    Nonblocking TCP Socket Server Class.
    Listen socket for incoming TCP connections that generates Incomer sockets
    for accepted connections

    Inherited Attributes:
        .ha is (host,port) duple (two tuple)
               host = "" or "0.0.0.0" means listen on all interfaces
        .eha is normalized (host, port) duple for incoming TLS connections
                as external facing address for TLS context
        .bs is buffer size
        .ss is server listen socket for incoming accept requests
        .axes is deque of accepte connection duples (ca, cs)
        .opened is boolean, True if listen socket .ss opened. False otherwise

    Attributes:
        .tymist is Tymist instance
        .timeout is timeout in seconds for connection refresh
        .wlog is wire log
        .ixes is dict of incoming connections indexed by remote (host, port) duple
    """

    Timeout = 1.0  # timeout in seconds

    def __init__(self,
                 ha=None,
                 host="",
                 port=56000,
                 tymist=None,
                 timeout=None,
                 wlog=None,
                 **kwa):
        """
        Initialization method for instance.
        Parameters:
            ha is TCP/IP (host, port) duple for listen socket
            host is default TCP/IP host address for listen socket
                "" or "0.0.0.0" is listen on all interfaces
            port is default TCP/IP port
            tymist is Tymist instance if any to pass to incomers for incoming connections
            timeout is default timeout for to pass to incomers for  incoming connections
            wlog is WireLog object if any
        """
        ha = ha or (host, port)
        super(Server, self).__init__(ha=ha, **kwa)
        self.tymist = tymist or tyming.Tymist()
        self.timeout = timeout if timeout is not None else self.Timeout
        self.wlog = wlog
        self.ixes = dict()  # ready to rx tx incoming connections, Incomer instances


    def serviceAxes(self):
        """
        Service axes

        For each newly accepted connection in .axes create Incomer
        and add to .ixes keyed by ca
        """
        self.serviceAccepts()  # populate .axes
        while self.axes:
            cs, ca = self.axes.popleft()
            if ca != cs.getpeername(): #or self.eha != cs.getsockname():
                raise ValueError("Accepted socket host addresses malformed for "
                                 "peer. eha {0} != {1}, ca {2} != {3}\n".format(
                                     self.eha, cs.getsockname(), ca, cs.getpeername()))
            incomer = Incomer(ha=cs.getsockname(),
                              ca=ca,
                              cs=cs,
                              bs=self.bs,
                              wlog=self.wlog,
                              tymist=self.tymist,
                              timeout=self.timeout)
            if ca in self.ixes and self.ixes[ca] is not incomer:
                self.shutdownIx[ca]
            self.ixes[ca] = incomer


    def serviceConnects(self):
        """
        Service connects is method name to be used
        """
        self.serviceAxes()


    def shutdownIx(self, ca, how=socket.SHUT_RDWR):
        """
        Shutdown incomer given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].shutdown(how=how)


    def shutdownSendIx(self, ca):
        """
        Shutdown send on incomer given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].shutdownSend()


    def shutdownReceiveIx(self, ca):
        """
        Shutdown send on incomer given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].shutdownReceive()


    def closeIx(self, ca):
        """
        Shutdown and close incomer given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].close()


    def closeAllIx(self):
        """
        Shutdown and close all incomer connections
        """
        for ix in self.ixes.values():
            ix.close()


    def close(self):
        """
        Close all sockets
        """
        super(Server, self).close()  #  call super close
        self.closeAllIx()


    def removeIx(self, ca, close=True):
        """
        Remove incomer given by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        if close:
            self.ixes[ca].close()  # shutdown and close socket
        del self.ixes[ca]


    def serviceReceivesIx(self, ca):
        """
        Service receives for incomer by connection address ca
        """
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].serviceReceives()


    def serviceReceivesAllIx(self):
        """
        Service receives for all incomers in .ixes
        """
        for ix in self.ixes.values():
            ix.serviceReceives()


    def transmitIx(self, data, ca):
        '''
        Queue data onto .txes for incomer given by connection address ca
        '''
        if ca not in self.ixes:
            emsg = "Invalid connection address '{0}'".format(ca)
            raise ValueError(emsg)
        self.ixes[ca].tx(data)


    def serviceTxesAllIx(self):
        """
        Service transmits for all incomers in .ixes
        """
        for ix in self.ixes.values():
            ix.serviceTxes()


    def serviceAll(self):
        """
        Service connects and service receives and txes for all ix.
        """
        self.serviceConnects()
        self.serviceReceivesAllIx()
        self.serviceTxesAllIx()



def initServerContext(context=None,
                      version=None,
                      certify=None,
                      keypath=None,
                      certpath=None,
                      cafilepath=None
                      ):
    """
    Initialize and return context for TLS Server
    IF context is None THEN create a context

    IF version is None THEN create context using ssl library default
    ELSE create context with version

    If certify is not None then use certify value provided Otherwise use default

    context = context object for tls/ssl If None use default
    version = ssl protocol version If None use default
    certify = cert requirement If None use default
              ssl.CERT_NONE = 0
              ssl.CERT_OPTIONAL = 1
              ssl.CERT_REQUIRED = 2
    keypath = pathname of local server side PKI private key file path
              If given apply to context
    certpath = pathname of local server side PKI public cert file path
              If given apply to context
    cafilepath = Cert Authority file path to use to verify client cert
              If given apply to context
    """
    if context is None:  # create context
        if not version:  # use default context with default protocol version
            context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            context.verify_mode = certify if certify is not None else ssl.CERT_REQUIRED

        else:  # create context with specified protocol version
            context = ssl.SSLContext(protocol=version)
            # disable bad protocols versions
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            # disable compression to prevent CRIME attacks (OpenSSL 1.0+)
            context.options |= getattr(ssl._ssl, "OP_NO_COMPRESSION", 0)
            # Prefer the server's ciphers by default fro stronger encryption
            context.options |= getattr(ssl._ssl, "OP_CIPHER_SERVER_PREFERENCE", 0)
            # Use single use keys in order to improve forward secrecy
            context.options |= getattr(ssl._ssl, "OP_SINGLE_DH_USE", 0)
            context.options |= getattr(ssl._ssl, "OP_SINGLE_ECDH_USE", 0)
            # disallow ciphers with known vulnerabilities
            context.set_ciphers(ssl._RESTRICTED_SERVER_CIPHERS)
            context.verify_mode = certify if certify is not None else ssl.CERT_REQUIRED

    if cafilepath:
        context.load_verify_locations(cafile=cafilepath,
                                      capath=None,
                                      cadata=None)
    elif context.verify_mode != ssl.CERT_NONE:
        context.load_default_certs(purpose=ssl.Purpose.CLIENT_AUTH)

    if keypath or certpath:
        context.load_cert_chain(certfile=certpath, keyfile=keypath)

    return context



class ServerTls(Server):
    """
    Server with Nonblocking TLS/SSL support
    Nonblocking TCP Socket Server Class.
    Listen socket for incoming TCP connections
    IncomerTLS sockets for accepted connections

    Inherited Attributes:
        .ha is (host,port) duple (two tuple)
               host = "" or "0.0.0.0" means listen on all interfaces
        .eha is normalized (host, port) duple for incoming TLS connections
                as external facing address for TLS context
        .bs is buffer size
        .ss is server listen socket for incoming accept requests
        .axes is deque of accepte connection duples (ca, cs)
        .opened is boolean, True if listen socket .ss opened. False otherwise
        .tymist is Tymist instance
        .timeout is timeout in seconds for connection refresh
        .wlog is wire log
        .ixes is dict of incoming connections indexed by remote (host, port) duple

    Attributes:
        .context is TLS context instance
        .version is TLS version
        .certify is boolean, True to client certify, False otherwise
        .keypath is path to key file
        .certpath is path to cert file
        .cafilepath is path to ca file
    """
    def __init__(self,
                 context=None,
                 version=None,
                 certify=None,
                 keypath=None,
                 certpath=None,
                 cafilepath=None,
                 **kwa):
        """
        Initialization method for instance.
        """
        super(ServerTls, self).__init__(**kwa)

        self.cxes = dict()  # accepted incoming connections, IncomerTLS instances

        self.context = context
        self.version = version
        self.certify = certify
        self.keypath = keypath
        self.certpath = certpath
        self.cafilepath = cafilepath

        self.context = initServerContext(context=context,
                                         version=version,
                                         certify=certify,
                                         keypath=keypath,
                                         certpath=certpath,
                                         cafilepath=cafilepath
                                        )


    def serviceAxes(self):
        """
        Service accepteds

        For each new accepted connection create IncomerTLS and add to .cxes
        Not Handshaked
        """
        self.serviceAccepts()  # populate .axes
        while self.axes:
            cs, ca = self.axes.popleft()
            if ca != cs.getpeername() or self.eha != cs.getsockname():
                raise ValueError("Accepted socket host addresses malformed for "
                                 "peer ha {0} != {1}, ca {2} != {3}\n".format(
                                     self.ha, cs.getsockname(), ca, cs.getpeername()))
            incomer = IncomerTls(ha=cs.getsockname(),
                                 ca=ca,
                                 bs=self.bs,
                                 cs=cs,
                                 wlog=self.wlog,
                                 tymist=self.tymist,
                                 timeout=self.timeout,
                                 context=self.context,
                                 version=self.version,
                                 certify=self.certify,
                                 keypath=self.keypath,
                                 certpath=self.certpath,
                                 cafilepath=self.cafilepath,
                                )

            self.cxes[ca] = incomer


    def serviceCxes(self):
        """
        Service handshakes for every incomer in .cxes
        If successful move to .ixes
        """
        for ca, cx in list(self.cxes.items()):
            if cx.serviceHandshake():
                self.ixes[ca] = cx
                del self.cxes[ca]


    def serviceConnects(self):
        """
        Service accept and handshake attempts
        If not already accepted and handshaked  Then
             make nonblocking attempt
        For each successful handshaked add to .ixes
        Returns handshakeds
        """
        self.serviceAxes()
        self.serviceCxes()


class Incomer(object):
    """
    Class to service incoming nonblocking TCP connections from remote client.
    Should only be used from Acceptor subclass
    """
    Timeout = 0.0  # timeout in seconds

    def __init__(self,
                 ha,
                 ca,
                 cs,
                 tymist=None,
                 timeout=None,
                 refreshable=True,
                 bs=8096,
                 wlog=None
                ):

        """
        Initialization method for instance.
        ha = host address duple (host, port) near side of connection. cs.getsockname()
             useful for debugging after cs is closed
        ca = connection address used as key in severs's ixes. Need this to
             know how to delete from .ixes when connection closed as .cs loses
             cs.getpeername() after its closed.
        cs = connection socket object
        tymist = Tymist instance
        timeout = timeout for .timer
        refreshable = True if tx/rx activity refreshes timer False otherwise
        bs = buffer size
        wlog = WireLog object if any
        """
        self.ha = ha  # connection address of server
        self.ca = ca  # connection address of peer used to index in server.ixes
        self.cs = cs  # connection socket
        if self.cs:
            self.cs.setblocking(0)  # linux does not preserve blocking from accept
        self.tymist = tymist or tyming.Tymist()
        self.timeout = timeout if timeout is not None else self.Timeout
        self.tymer = tyming.Tymer(tymist=self.tymist, duration=self.timeout)


        self.cutoff = False # True when detect connection closed on far side
        self.refreshable = refreshable
        self.bs = bs
        self.txes = deque()  # deque of data to send
        self.rxbs = bytearray()  # bytearray of data received
        self.wlog = wlog


    def shutdown(self, how=socket.SHUT_RDWR):
        """
        Shutdown connected socket .cs
        """
        if self.cs:
            try:
                self.cs.shutdown(how)  # shutdown socket
            except socket.error as ex:
                pass


    def shutdownSend(self):
        """
        Shutdown send on connected socket .cs
        """
        if self.cs:
            try:
                self.shutdown(how=socket.SHUT_WR)  # shutdown socket
            except socket.error as ex:
                pass


    def shutdownReceive(self):
        """
        Shutdown receive on connected socket .cs
        """
        if self.cs:
            try:
                self.shutdown(how=socket.SHUT_RD)  # shutdown socket
            except socket.error as ex:
                pass


    def close(self):
        """
        Shutdown and close connected socket .cs
        """
        if self.cs:
            self.shutdown()
            self.cs.close()  #close socket
            self.cs = None


    def refresh(self):
        """
        Restart tymer
        """
        self.tymer.restart()


    def receive(self):
        """
        Perform non blocking receive on connected socket .cs

        If no data then returns None
        If connection closed then returns ''
        Otherwise returns data

        data is string in python2 and bytes in python3
        """
        try:
            data = self.cs.recv(self.bs)
        except socket.error as ex:
            # ex.args[0] is always ex.errno for better compat
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                return None  # keep trying
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED):
                self.cutoff = True  # this signals need to close/reopen connection
                return bytes()  # data empty
            else:
                raise  # re-raise

        if data:  # connection open
            if self.wlog:  # log over the wire rx
                self.wlog.writeRx(self.ca, data)

            if self.refreshable:
                self.refresh()

        else:  # data empty so connection closed on other end
            self.cutoff = True

        return data


    def serviceReceives(self):
        """
        Service receives until no more
        """
        while not self.cutoff:
            data = self.receive()
            if not data:
                break
            self.rxbs.extend(data)


    def serviceReceiveOnce(self):
        '''
        Retrieve from server only one reception
        '''
        if not self.cutoff:
            data = self.receive()
            if data:
                self.rxbs.extend(data)


    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs[:]


    def send(self, data):
        """
        Perform non blocking send on connected socket .cs.
        Return number of bytes sent

        data is string in python2 and bytes in python3
        """
        try:
            result = self.cs.send(data) #result is number of bytes sent
        except socket.error as ex:
            # ex.args[0] is always ex.errno for better compat
            if ex.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                result = 0  # blocked try again
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED):
                self.cutoff = True  # this signals need to close/reopen connection
                result = 0
            else:
                raise

        if result:
            if self.wlog:
                self.wlog.writeTx(self.ca, data[:result])

            if self.refreshable:
                self.refresh()

        return result


    def tx(self, data):
        '''
        Queue data onto .txes
        '''
        self.txes.append(data)


    def serviceTxes(self):
        """
        Service transmits
        For each tx if all bytes sent then keep sending until partial send
        or no more to send
        If partial send reattach and return
        """
        while self.txes and not self.cutoff:
            data = self.txes.popleft()
            count = self.send(data)
            if count < len(data):  # put back unsent portion
                self.txes.appendleft(data[count:])
                break  # try again later


class IncomerTls(Incomer):
    """
    Incomer with Nonblocking TLS/SSL support
    Manager class for incoming nonblocking TCP connections.
    """
    def __init__(self,
                 context=None,
                 version=None,
                 certify=None,
                 keypath=None,
                 certpath=None,
                 cafilepath=None,
                 **kwa):

        """
        Initialization method for instance.
        context = context object for tls/ssl If None use default
        version = ssl version If None use default
        certify = cert requirement If None use default
                  ssl.CERT_NONE = 0
                  ssl.CERT_OPTIONAL = 1
                  ssl.CERT_REQUIRED = 2
        keypath = pathname of local server side PKI private key file path
                  If given apply to context
        certpath = pathname of local server side PKI public cert file path
                  If given apply to context
        cafilepath = Cert Authority file path to use to verify client cert
                  If given apply to context
        """
        super(IncomerTls, self).__init__(**kwa)

        self.connected = False  # True once ssl handshake completed

        self.context = initServerContext(context=context,
                                    version=version,
                                    certify=certify,
                                    keypath=keypath,
                                    certpath=certpath,
                                    cafilepath=cafilepath
                                  )
        self.wrap()


    def close(self):
        """
        Shutdown and close connected socket .cs
        """
        if self.cs:
            self.shutdown()
            self.cs.close()  #close socket
            self.cs = None
            self.connected = False


    def wrap(self):
        """
        Wrap socket .cs in ssl context
        """
        self.cs = self.context.wrap_socket(self.cs,
                                           server_side=True,
                                           do_handshake_on_connect=False)


    def handshake(self):
        """
        Attempt nonblocking ssl handshake to .ha
        Returns True if successful
        Returns False if not so try again later
        """
        try:
            self.cs.do_handshake()
        except ssl.SSLError as ex:
            if ex.errno in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                return False
            elif ex.errno in (ssl.SSL_ERROR_EOF, ):
                self.shutclose()
                raise   # should give up here nicely
            else:
                self.shutclose()
                raise
        except OSError as ex:
            self.shutclose()
            if ex.errno in (errno.ECONNABORTED, ):
                raise  # should give up here nicely
            raise
        except Exception as ex:
            self.shutclose()
            raise

        self.connected = True
        return True


    def serviceHandshake(self):
        """
        Service connection and handshake attempt
        If not already accepted and handshaked  Then
             make nonblocking attempt
        Returns .handshaked
        """
        if not self.connected:
            self.handshake()

        return self.connected


    def receive(self):
        """
        Perform non blocking receive on connected socket .cs

        If no data then returns None
        If connection closed then returns ''
        Otherwise returns data

        data is string in python2 and bytes in python3
        """
        try:
            data = self.cs.recv(self.bs)
        except socket.error as ex:  # ssl.SSLError is a subtype of socket.error
            # ex.args[0] is always ex.errno for better compat
            if  ex.args[0] in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                return None  # blocked waiting for data
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED,
                                ssl.SSLEOFError):
                self.cutoff = True  # this signals need to close/reopen connection
                return bytes()  # data empty
            else:
                raise  # re-raise

        if data:  # connection open
            if self.wlog:  # log over the wire rx
                self.wlog.writeRx(self.cs.getpeername(), data)

        else:  # data empty so connection closed on other end
            self.cutoff = True

        return data


    def send(self, data):
        """
        Perform non blocking send on connected socket .cs.
        Return number of bytes sent

        data is string in python2 and bytes in python3
        """
        try:
            result = self.cs.send(data) #result is number of bytes sent
        except socket.error as ex:  # ssl.SSLError is a subtype of socket.error
            # ex.args[0] is always ex.errno for better compat
            if ex.args[0] in (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE):
                result = 0  # blocked try again
            elif ex.args[0] in (errno.ECONNRESET,
                                errno.ENETRESET,
                                errno.ENETUNREACH,
                                errno.EHOSTUNREACH,
                                errno.ENETDOWN,
                                errno.EHOSTDOWN,
                                errno.ETIMEDOUT,
                                errno.ECONNREFUSED,
                                ssl.SSLEOFError):
                self.cutoff = True  # this signals need to close/reopen connection
                result = 0
            else:
                raise

        if result:
            if self.wlog:
                self.wlog.writeTx(self.cs.getpeername(), data[:result])

        return result
