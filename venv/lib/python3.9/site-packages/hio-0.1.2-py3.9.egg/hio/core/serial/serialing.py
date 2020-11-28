"""
Asynchronous (nonblocking) serial io

"""
from __future__ import absolute_import, division, print_function

import sys
import os
import errno
from collections import deque

from ... hioing import HioError


class LineError(HioError):
    """
    Serial line error. Too big for buffer.

    Usage:
        raise LineError("error message")
    """

class Console():
    """
    Class to manage non blocking io on serial console in canonical mode.

    Opens non blocking read file descriptor on console
    Use instance method .close to close file descriptor
    Use instance methods .getline & .put to read & write to console
    Needs os module

    Attributes:
        .bs is max buffer size for each read
        .fd  is file descriptor for console
        .opened is Boolean that indicates open state of .fd

    Methods:
        .reopen  closes and reopens .fd, sets .opened
        .close   closes .fd unsets .opened
        .getLine  gets one newline terminated line or bs characters
        .put  puts characters

    Hidden:
        ._line is bytearray of line buffer

    """
    MaxBufSize = 256

    def __init__(self, bs=None):
        """
        Initialization method for instance.
        Creates attributes.
        """
        self.bs = bs if bs is not None else self.MaxBufSize
        self.fd = None  # console file descriptor needs to be opened
        self.opened =  False
        self._line = bytearray()


    def reopen(self, port=''):
        """
        Opens fd on terminal console in non blocking mode.

        port is the serial port device path name
        or if '' then use os.ctermid() which
        returns path name of console usually '/dev/tty'

        os.O_NONBLOCK makes non blocking io
        os.O_RDWR allows both read and write.
        os.O_NOCTTY don't make this the controlling terminal of the process
        O_NOCTTY is only for cross platform portability BSD never makes it the
        controlling terminal

        Don't use print at same time since it will mess up non blocking reads.

        Input mode assumes Canonical means no characters available until a newline
        It appears that canonical mode only applies to the console os.ctermid().
        For other serial ports the characters are available immediately.

        os.isatty(fd)
        Return True if the file descriptor fd is open and connected to a
        tty(-like) device, else False.

        """
        self.close()  # ensure closed first before reopening

        if not port:
            port = os.ctermid()  # default to console

        try:
            self.fd = os.open(port, os.O_NONBLOCK | os.O_RDWR | os.O_NOCTTY)
        except OSError as ex:
            # maybe complain here
            return False

        self.opened = True
        return self.opened


    def close(self):
        """
        Closes fd.
        """
        if self.fd:
            os.close(self.fd)
            self.fd = None
        del self._line[:]
        self.opened = False


    def put(self, data = b'\n'):
        """
        Writes data bytes to console and return number of bytes from data written.
        """
        return (os.write(self.fd, data))  # returns number of bytes written


    def getLine(self, bs=None):
        """
        Gets nonblocking line of bytes from console
        of up to bs characters with eol newline if in bs characters

        Returns empty string if no characters available else returns line.
        Assumes canonical mode where no chars available to read until eol newline
        is entered and eol is included in the read characters.

        Strips eol newline before returning line.
        """
        bs = bs if bs is not None else self.bs
        line = bytearray()
        try:
            self._line.extend(os.read(self.fd, bs))
        except OSError as ex1:  #if no chars available generates exception
            try:  # need to catch correct exception
                errno = ex1.args[0]  # if args not sequence get TypeError
                if errno == 35:
                    pass  # No characters available
                else:
                    raise  # re raise exception ex1

            except TypeError as ex2:  # catch args[0] mismatch above
                raise ex1  # ignore TypeError, re-raise exception ex1
        else:
            if self._line[-1] == ord(b'\n'):  # got full line so return it
                del self._line[-1]  # delete eol newline
                line.extend(self._line)
                del self._line[:]

        return line


class ConsoleServer(Console):
    """
    Class that extends Console with service interface.


    Inherited Attributes:
        .bs is max buffer size for each read
        .fd  is file descriptor for console
        .opened is Boolean that indicates open state of .fd

    Attributes:
        .puts is bytearray of bytes to put on serial port
        .lines is deque of lines of bytes gotten from serial port
                  each line has newline stripped.

    Methods:
        .reopen  closes and reopens .fd, sets .opened
        .close   closes .fd unsets .opened
        .getLine  gets one newline terminated line or bs characters
        .put  puts characters

        .servicePuts
        .serviceLines
        .serviceAll

    Hidden:
        Hidden:
        ._line is bytearray of line buffer
    """

    def __init__(self, puts=None, lines=None, **kwa):
        """
        Initialization method for instance.
        Creates attributes.
        """
        super(ConsoleServer, self).__init__(**kwa)
        self.puts = puts if puts is not None else bytearray()
        self.lines = lines if lines is not None else deque()


    def servicePuts(self):
        """
        Service .puts by putting to serial port
        """
        count = self.put(data=self.puts)
        del self.puts[:count]


    def serviceLines(self):
        """
        Service .lines by getting line from serial port
        """
        if (line := self.getLine()):
            self.lines.append(line)


    def serviceAll(self):
        """
        Service puts and lines
        """
        self.servicePuts()
        self.serviceLines()


class Device():
    """
    Class to manage non blocking IO on serial device port.

    Opens non blocking read file descriptor on serial port
    Use instance method close to close file descriptor
    Use instance methods get & put to read & write to serial device
    Needs os module
    """

    def __init__(self, port=None, speed=9600, bs=1024):
        """
        Initialization method for instance.

        port = serial device port path string
        speed = serial port speed in bps
        bs = buffer size for reads
        """
        self.fd = None #serial device port file descriptor, must be opened first
        self.port = port or os.ctermid() #default to console
        self.speed = speed or 9600
        self.bs = bs or 1024
        self.opened = False

    def reopen(self, port=None, speed=None, bs=None):
        """
        Idempotently open serial device port
        Opens fd on serial port in non blocking mode.

        port is the serial port device path name or
        if '' then use os.ctermid() which
        returns path name of console usually '/dev/tty'

        os.O_NONBLOCK makes non blocking io
        os.O_RDWR allows both read and write.
        os.O_NOCTTY don't make this the controlling terminal of the process
        O_NOCTTY is only for cross platform portability BSD never makes it the
        controlling terminal

        Don't use print and console at same time since it will mess up non blocking reads.

        The input mode, canonical or noncanonical, is controlled by the
        ICANON flag see termios module.

        Raw mode

        def setraw(fd, when=TCSAFLUSH):
            Put terminal into a raw mode.
            mode = tcgetattr(fd)
            mode[IFLAG] = mode[IFLAG] & ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
            mode[OFLAG] = mode[OFLAG] & ~(OPOST)
            mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
            mode[CFLAG] = mode[CFLAG] | CS8
            mode[LFLAG] = mode[LFLAG] & ~(ECHO | ICANON | IEXTEN | ISIG)
            mode[CC][VMIN] = 1
            mode[CC][VTIME] = 0
            tcsetattr(fd, when, mode)


        # set up raw mode / no echo / binary
        cflag |=  (TERMIOS.CLOCAL|TERMIOS.CREAD)
        lflag &= ~(TERMIOS.ICANON|TERMIOS.ECHO|TERMIOS.ECHOE|TERMIOS.ECHOK|TERMIOS.ECHONL|
                     TERMIOS.ISIG|TERMIOS.IEXTEN) #|TERMIOS.ECHOPRT
        for flag in ('ECHOCTL', 'ECHOKE'): # netbsd workaround for Erk
            if hasattr(TERMIOS, flag):
                lflag &= ~getattr(TERMIOS, flag)

        oflag &= ~(TERMIOS.OPOST)
        iflag &= ~(TERMIOS.INLCR|TERMIOS.IGNCR|TERMIOS.ICRNL|TERMIOS.IGNBRK)
        if hasattr(TERMIOS, 'IUCLC'):
            iflag &= ~TERMIOS.IUCLC
        if hasattr(TERMIOS, 'PARMRK'):
            iflag &= ~TERMIOS.PARMRK

        """
        self.close()

        if port is not None:
            self.port = port
        if speed is not None:
            self.speed = speed
        if bs is not None:
            self.bs = bs

        self.fd = os.open(self.port, os.O_NONBLOCK | os.O_RDWR | os.O_NOCTTY)

        system = platform.system()

        if (system == 'Darwin') or (system == 'Linux'):  # use termios to set values
            import termios

            iflag, oflag, cflag, lflag, ispeed, ospeed, cc = range(7)

            settings = termios.tcgetattr(self.fd)
            #print(settings)

            settings[lflag] = (settings[lflag] & ~termios.ICANON)

            settings[lflag] = (settings[lflag] & ~termios.ECHO) # no echo

            #ignore carriage returns on input
            #settings[iflag] = (settings[iflag] | (termios.IGNCR)) #ignore cr

            # 8N1 8bit word no parity one stop bit nohardware handshake ctsrts
            # to set size have to mask out(clear) CSIZE bits and or in size
            settings[cflag] = ((settings[cflag] & ~termios.CSIZE) | termios.CS8)
            # no parity clear PARENB
            settings[cflag] = (settings[cflag] & ~termios.PARENB)
            #one stop bit clear CSTOPB
            settings[cflag] = (settings[cflag] & ~termios.CSTOPB)
            #no hardware handshake clear crtscts
            settings[cflag] = (settings[cflag] & ~termios.CRTSCTS)

            # in linux the speed flag does not equal value so always set it
            speedattr = "B{0}".format(self.speed)  # convert numeric speed to attribute name string
            speed = getattr(termios, speedattr)
            settings[ispeed] = speed
            settings[ospeed] = speed

            termios.tcsetattr(self.fd, termios.TCSANOW, settings)
            #print(settings)

        self.opened = True

        return self.opened



    def close(self):
        """
        Closes fd.

        """
        if self.fd:
            os.close(self.fd)
            self.fd = None
            self.opened = False


    def receive(self):
        """
        Reads nonblocking characters from serial device up to bs characters
        Returns empty bytes if no characters available else returns all available.
        In canonical mode no chars are available until newline is entered.
        """
        data = b''
        try:
            data = os.read(self.fd, self.bs)  #if no chars available generates exception
        except OSError as ex1:  # ex1 is the target instance of the exception
            if ex1.errno == errno.EAGAIN: #BSD 35, Linux 11
                pass #No characters available
            else:
                raise #re raise exception ex1

        return data

    def send(self, data=b'\n'):
        """
        Writes data bytes to serial device port.
        Returns number of bytes sent
        """
        try:
            count = os.write(self.fd, data)
        except OSError as ex1:  # ex1 is the target instance of the exception
            if ex1.errno == errno.EAGAIN: #BSD 35, Linux 11
                count = 0  # buffer full can't write
            else:
                raise #re raise exception ex1

        return count


class Serial():
    """
    Class to manage non blocking IO on serial device port using pyserial

    Opens non blocking read file descriptor on serial port
    Use instance method close to close file descriptor
    Use instance methods get & put to read & write to serial device
    Needs os module
    """

    def __init__(self, port=None, speed=9600, bs=1024):
        """
        Initialization method for instance.

        port = serial device port path string
        speed = serial port speed in bps
        bs = buffer size for reads


        """
        self.serial = None  # Serial instance
        self.port = port or os.ctermid() #default to console
        self.speed = speed or 9600
        self.bs = bs or 1024
        self.opened = False

    def reopen(self, port=None, speed=None, bs=None):
        """
        Opens fd on serial port in non blocking mode.

        port is the serial port device path name or
        if None then use os.ctermid() which returns path name of console
        usually '/dev/tty'
        """
        self.close()

        if port is not None:
            self.port = port
        if speed is not None:
            self.speed = speed
        if bs is not None:
            self.bs = bs

        import serial  # import pyserial
        self.serial = serial.Serial(port=self.port,
                                    baudrate=self.speed,
                                    timeout=0,
                                    writeTimeout=0)
        #self.serial.nonblocking()
        self.serial.reset_input_buffer()
        self.opened = True

        return self.opened


    def close(self):
        """
        Closes .serial
        """
        if self.serial:
            self.serial.reset_output_buffer()
            self.serial.close()
            self.serial = None
            self.opened = False

    def receive(self):
        """
        Reads nonblocking characters from serial device up to bs characters
        Returns empty bytes if no characters available else returns all available.
        In canonical mode no chars are available until newline is entered.
        """
        data = b''
        try:
            data = self.serial.read(self.bs)  #if no chars available generates exception
        except OSError as ex1:  # ex1 is the target instance of the exception
            if ex1.errno == errno.EAGAIN: #BSD 35, Linux 11
                pass #No characters available
            else:
                raise #re raise exception ex1

        return data

    def send(self, data=b'\n'):
        """
        Writes data bytes to serial device port.
        Returns number of bytes sent
        """
        try:
            count = self.serial.write(data)
        except OSError as ex1:  # ex1 is the target instance of the exception
            if ex1.errno == errno.EAGAIN: #BSD 35, Linux 11
                count = 0  # buffer full can't write
            else:
                raise #re raise exception ex1

        return count



class Driver():
    """
    Nonblocking Serial Device Port Driver
    """

    def __init__(self,
                 name=u'',
                 uid=0,
                 port=None,
                 speed=9600,
                 bs=1024,
                 server=None):
        """
        Initialization method for instance.

        Parameters:
            name = user friendly name for driver
            uid = unique identifier for driver
            port = serial device port path string
            speed = serial port speed in bps
            canonical = canonical mode True or False
            bs = buffer size for reads
            server = serial port device server if any

        Attributes:
           name = user friendly name for driver
           uid = unique identifier for driver
           server = serial device server nonblocking
           txes = deque of data bytes to send
           rxbs = bytearray of data bytes received

        """
        self.name = name
        self.uid = uid

        if not server:
            try:
                import serial
                self.server = SerialNb(port=port,
                                       speed=speed,
                                       bs=bs)

            except ImportError as  ex:
                console.terse("Error: importing pyserial\n{0}\n".format(ex))
                self.server = DeviceNb(port=port,
                                       speed=speed,
                                       bs=bs)
        else:
            self.server = server

        self.txes = deque()  # deque of data to send
        self.rxbs = bytearray()  # byte array of data received

    def serviceReceives(self):
        """
        Service receives until no more
        """
        while self.server.opened:
            data = self.server.receive()  # bytes
            if not data:
                break
            self.rxbs.extend(data)

    def serviceReceiveOnce(self):
        '''
        Retrieve from server only one reception
        '''
        if self.server.opened:
            data = self.server.receive()
            if data:
                self.rxbs.extend(data)

    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs[:]

    def scan(self, start):
        """
        Returns offset of given start byte in self.rxbs
        Returns None if start is not given or not found
        If strip then remove any bytes before offset
        """
        offset = self.rxbs.find(start)
        if offset < 0:
            return None
        return offset

    def tx(self, data):
        '''
        Queue data onto .txes
        '''
        self.txes.append(data)

    def _serviceOneTx(self):
        """
        Handle one tx data
        """
        data = self.txes.popleft()
        count = self.server.send(data)
        if count < len(data):  # put back unsent portion
            self.txes.appendleft(data[count:])
            return False  # blocked
        console.profuse("{0}: Sent: {1}\n".format(self.name, data))
        return True  # send more


    def serviceTxes(self):
        """
        Service txes data
        """
        while self.txes and self.server.opened:
            again = self._serviceOneTx()
            if not again:
                break  # blocked try again later


    def serviceTxOnce(self):
        '''
        Service one data on the .txes deque to send through device
        '''
        if self.txes and self.server.opened:
            self._serviceOneTx()


