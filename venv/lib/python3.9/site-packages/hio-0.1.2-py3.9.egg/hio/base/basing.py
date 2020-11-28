# -*- encoding: utf-8 -*-
"""
hio.base.basing Module
"""
import enum
from collections import  namedtuple


State = namedtuple("State", "tyme context feed count")

Ctl = enum.Enum('Control', 'enter recur exit abort')
Stt = enum.Enum('State', 'entered recurring exited aborted')

