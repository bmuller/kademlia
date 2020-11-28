# -*- encoding: utf-8 -*-
"""
keri.help.ogling module

Provides python stdlib logging module support

"""
import os
import logging
import tempfile
import shutil

ogler = None  # module global ogler instance used by all for keri console logging


def initOgler(level=logging.CRITICAL, **kwa):
    """
    Initialize the ogler global instance once
    Critical is most severe to restrict logging by default

    This should be called in package .__init__ to insure that global ogler is
    define by default. Users and then reset level and reopen log file if need be
    before calling ogler.getLoggers()
    """
    global ogler
    if ogler is None:
        ogler = Ogler(level=level, **kwa)

    return ogler


class Ogler():
    """
    Olgery instances are logger factories that configure and build loggers
    Only need one Ogler per application

    logging.getLogger(name). Multiple calls to getLogger() with the same name
    will always return a reference to the same Logger object.

    Attributes:
        .level is logging severity level
        .logFilePath is path to log file
    """
    HeadDirPath = "/usr/local/var"  # default in /usr/local/var
    TailDirPath = "keri/log"
    AltHeadDirPath = "~"  #  put in ~ as fallback when desired not permitted
    AltTailDirPath = ".keri/log"

    def __init__(self, name='main', level=logging.ERROR, temp=False,
                 headDirPath=None, reopen=False):
        """
        Init Loggery factory instance

        Parameters:
            name is application specific log file name
            level is int logging level from logging. Higher is more restrictive.
                This sets the minimum level of the baseLogger and failLogger
                relative to the global level.
                Logs will output if action level is at or above set level.

                Level    Numeric value
                CRITICAL 50
                ERROR    40
                WARNING  30
                INFO     20
                DEBUG    10
                NOTSET    0

            file is Boolean True means create logfile Otherwise not
            temp is Boolean If file then True means use temp direction
                                         Otherwise use  headDirpath
            headDirPath is str for custom headDirPath for log file

        """
        self.name = name
        self.level = level  # basic logger level
        self.temp = True if temp else False
        self.headDirPath = headDirPath
        self.path = None
        self.opened = False

        #create formatters
        self.baseFormatter = logging.Formatter('%(message)s')  # basic format
        self.failFormatter = logging.Formatter('***Fail: %(message)s')  # failure format

        #create console handlers and assign formatters
        self.baseConsoleHandler = logging.StreamHandler()  # sys.stderr
        self.baseConsoleHandler.setFormatter(self.baseFormatter)
        self.failConsoleHandler = logging.StreamHandler()  # sys.stderr
        self.failConsoleHandler.setFormatter(self.failFormatter)

        if reopen:
            self.reopen(headDirPath=self.headDirPath)



    def reopen(self, temp=None, headDirPath=None):
        """
        Use or Create if not preexistent, directory path for lmdb at .path
        Open lmdb and assign to .env

        Parameters:
            temp is optional boolean:
                If None ignore Otherwise
                    Assign to .temp
                    If True then open temporary directory, clear on close
                    If False then open persistent directory, do not clear on close
            headDirPath is optional str head directory pathname of main database
                If not provided use default .HeadDirpath
        """
        if temp is not None:
            self.temp = True if temp else False

        if headDirPath is None:
            headDirPath = self.headDirPath

        if self.temp:
            headDirPath = tempfile.mkdtemp(prefix="keri_log_", suffix="_test", dir="/tmp")
            self.path = os.path.abspath(
                                os.path.join(headDirPath,
                                             self.TailDirPath))
            os.makedirs(self.path)

        else:
            if not headDirPath:
                headDirPath = self.HeadDirPath

            self.path = os.path.abspath(
                                os.path.expanduser(
                                    os.path.join(headDirPath,
                                                 self.TailDirPath)))

            if not os.path.exists(self.path):
                try:
                    os.makedirs(self.path)
                except OSError as ex:
                    headDirPath = self.AltHeadDirPath
                    self.path = os.path.abspath(
                                        os.path.expanduser(
                                            os.path.join(headDirPath,
                                                         self.AltTailDirPath)))
                    if not os.path.exists(self.path):
                        os.makedirs(self.path)
            else:
                if not os.access(self.path, os.R_OK | os.W_OK):
                    headDirPath = self.AltHeadDirPath
                    self.path = os.path.abspath(
                                        os.path.expanduser(
                                            os.path.join(headDirPath,
                                                         self.AltTailDirPath)))
                    if not os.path.exists(self.path):
                        os.makedirs(self.path)

        fileName = "{}.log".format(self.name)
        self.path = os.path.join(self.path, fileName)

        #create file handlers and assign formatters
        self.baseFileHandler = logging.FileHandler(self.path)
        self.baseFileHandler.setFormatter(self.baseFormatter)
        self.failFileHandler = logging.FileHandler(self.path)
        self.failFileHandler.setFormatter(self.failFormatter)

        self.opened = True


    def close(self, clear=False):
        """
        Close lmdb at .env and if clear or .temp then remove lmdb directory at .path
        Parameters:
           clear is boolean, True means clear lmdb directory
        """
        self.opened = False
        if clear or self.temp:
            self.clearDirPath()

    def clearDirPath(self):
        """
        Remove logfile directory at .path
        """
        if os.path.exists(self.path):
            shutil.rmtree(os.path.dirname(self.path))


    def getBlogger(self, name=__name__, level=None):
        """
        Returns Basic Logger
        default is to name logger after module
        """
        blogger = logging.getLogger(name)
        blogger.propagate = False  # disable propagation of events
        level = level if level is not None else self.level
        blogger.setLevel(level)
        for handler in blogger.handlers:  # remove so no duplicate handlers
            blogger.removeHandler(handler)
        blogger.addHandler(self.baseConsoleHandler)
        if self.opened:
            blogger.addHandler(self.baseFileHandler)
        return blogger

    def getFlogger(self, name=__name__, level=None):
        """
        Returns Failure Logger
        Since loggers are singletons by name we have to use unique name if
            we want to use different log format so we append .fail to base name
        """
        # Since loggers are singletons by name we have to change name if we
        # want to use different log format
        flogger = logging.getLogger("%s.%s" % (name, 'fail'))
        flogger.propagate = False  # disable propagation of events
        level = level if level is not None else self.level
        flogger.setLevel(max(level, logging.ERROR))
        for handler in flogger.handlers:  # remove so no duplicate handlers
            flogger.removeHandler(handler)
        flogger.addHandler(self.failConsoleHandler)  # output to console
        if self.opened:
            flogger.addHandler(self.failFileHandler)  # output to file
        return flogger

    def getLoggers(self, name=__name__):
        """
        Returns duple (blogger, flogger) of basic and failure loggers
        """
        return (self.getBlogger(name), self.getFlogger(name))

