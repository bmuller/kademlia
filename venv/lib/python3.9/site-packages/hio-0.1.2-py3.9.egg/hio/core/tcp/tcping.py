# -*- encoding: utf-8 -*-
"""
hio.core.tcping Module
"""

class Peer(Server):
    """
    Nonblocking TCP Socket Peer Class.
    Supports both incoming and outgoing connections.
    """
    def __init__(self, **kwa):
        """
        Initialization method for instance.
        """
        super(Peer, self).init(**kwa)

        self.oxes = odict()  # outgoers indexed by ha
