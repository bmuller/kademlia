# -*- encoding: utf-8 -*-
"""
hio.help.helping module

"""

import types
import functools


def copy_func(f, name=None):
    """
    Copy a function in detail.
    To change name of func provide name parameter

    functools to update_wrapper assigns and updates following attributes
    WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__',
                       '__annotations__')
    WRAPPER_UPDATES = ('__dict__',)
    Based on
    https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python
    https://stackoverflow.com/questions/13503079/how-to-create-a-copy-of-a-python-function
    """
    g = types.FunctionType(f.__code__,
                           f.__globals__,
                           name=f.__name__,
                           argdefs=f.__defaults__,
                           closure=f.__closure__
                          )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    if name:
        g.__name__ = name
    return g

