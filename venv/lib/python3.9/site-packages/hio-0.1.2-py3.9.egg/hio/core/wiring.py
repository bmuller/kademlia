# -*- encoding: utf-8 -*-
"""
hio.help.wiring module

"""

import os
import time
import io


class WireLog():
    """
    For debugging of non-blocking transports, provides log files or in memory
    buffers for logging 'over the wire' network tx and rx packets
    """
    def __init__(self,
                 path='',
                 prefix='',
                 midfix='',
                 rx=True,
                 tx=True,
                 same=False,
                 buffify=False):
        """
        Initialization method for instance.
        path = directory for log files
        prefix = prefix to include in log name if provided
        midfix = another more prefix for log name if provided
        rx = Boolean create rx log file if True
        tx = Boolean create tx log file if True
        same = Boolean use same log file for both rx and tx
        buffify = Boolean use BytesIO in memory buffer instead of File object
        """
        self.path = path  # path to directory where log files go must end in /
        self.prefix = prefix
        self.midfix = midfix
        self.rx = True if rx else False
        self.tx = True if tx else False
        self.same = True if same else False
        self.rxLog = None  # receive log file
        self.txLog = None  # transmit log file
        self.buffify = True if buffify else False

    def reopen(self, path='', prefix='', midfix=''):
        """
        Close and then open log files on path if given otherwise self.path
        Use ha in log file name if given
        """
        self.close()

        if path:
            self.path = path

        if prefix:
            self.prefix = prefix

        if midfix:
            self.midfix = midfix

        prefix = "{0}_".format(self.prefix) if self.prefix else ""
        midfix = "{0}_".format(self.midfix) if self.midfix else ""

        date = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time()))

        if self.same and (self.rx or self.tx):
            if not self.buffify:
                name = "{0}{1}{2}.txt".format(prefix, midfix, date)
                path = os.path.join(self.path, name)
                try:
                    log = io.open(path, mode='wb+')
                    if self.rx:
                        self.rxLog = log
                    if self.tx:
                        self.txLog = log
                except IOError:
                    self.rxLog = self.txLog = None
                    return False
            else:
                try:
                    log = io.BytesIO()
                    if self.rx:
                        self.rxLog = log
                    if self.tx:
                        self.txLog = log
                except IOError:
                    self.rxLog = self.txLog = None
                    return False

        else:
            if self.rx:
                if not self.buffify:
                    name = "{0}{1}{2}_rx.txt".format(prefix, midfix, date)
                    path = os.path.join(self.path, name)
                    try:
                        self.rxLog = io.open(path, mode='wb+')
                    except IOError:
                        self.rxLog = None
                        return False
                else:
                    try:
                        self.rxLog = io.BytesIO()
                    except IOError:
                        self.rxLog = None
                        return False

            if self.tx:
                if not self.buffify:
                    name = "{0}{1}{2}_tx.txt".format(prefix, midfix, date)
                    path = os.path.join(self.path, name)
                    try:
                        self.txLog = io.open(path, mode='wb+')
                    except IOError:
                        self.txLog = None
                        return False
                else:
                    try:
                        self.txLog = io.BytesIO()
                    except IOError:
                        self.txLog = None
                        return False

        return True

    def close(self):
        """
        Close log files
        """
        if self.txLog and not self.txLog.closed:
            self.txLog.close()
        if self.rxLog and not self.rxLog.closed:
            self.rxLog.close()

    def getRx(self):
        """
        Returns rx string buffer value if .buffify else None
        """
        if self.buffify and self.rxLog and not self.rxLog.closed:
            return (self.rxLog.getvalue())
        return None

    def getTx(self):
        """
        Returns tx string buffer value if .buffify else None
        """
        if self.buffify and self.txLog and not self.txLog.closed:
            return (self.txLog.getvalue())
        return None

    def writeRx(self, sa, data):
        """
        Write bytes data received from source address sa,
        """
        if self.rx and self.rxLog:
            self.rxLog.write(ns2b("RX {0}\n".format(sa)))
            self.rxLog.write(data)
            self.rxLog.write(b'\n')

    def writeTx(self, da, data):
        """
        Write bytes data transmitted to destination address da,
        """
        if self.tx and self.txLog:
            self.txLog.write(ns2b("TX {0}\n".format(da)))
            self.txLog.write(data)
            self.txLog.write(b'\n')
