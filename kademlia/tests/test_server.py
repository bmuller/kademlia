import unittest

from kademlia.network import Server
from kademlia.protocol import KademliaProtocol


class SwappableProtocolTests(unittest.TestCase):

    def test_default_protocol(self):
        """
        An ordinary Server object will initially not have a protocol, but will
        have a KademliaProtocol object as its protocol after its listen()
        method is called.
        """
        server = Server()
        self.assertIsNone(server.protocol)
        server.listen(8469)
        self.assertIsInstance(server.protocol, KademliaProtocol)
        server.stop()

    def test_custom_protocol(self):
        """
        A subclass of Server which overrides the protocol_class attribute will
        have an instance of that class as its protocol after its listen()
        method is called.
        """

        # Make a custom Protocol and Server to go with hit.
        class CoconutProtocol(KademliaProtocol):
            pass

        class HuskServer(Server):
            protocol_class = CoconutProtocol

        # An ordinary server does NOT have a CoconutProtocol as its protocol...
        server = Server()
        server.listen(8469)
        self.assertNotIsInstance(server.protocol, CoconutProtocol)
        server.stop()

        # ...but our custom server does.
        husk_server = HuskServer()
        husk_server.listen(8469)
        self.assertIsInstance(husk_server.protocol, CoconutProtocol)
        husk_server.stop()
