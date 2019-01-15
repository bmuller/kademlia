import unittest
import asyncio

import pytest

from kademlia.network import Server
from kademlia.protocol import KademliaProtocol


@pytest.mark.asyncio
async def test_storing(bootstrap_node):
    server = Server()
    await server.listen(bootstrap_node[1] + 1)
    await server.bootstrap([bootstrap_node])
    await server.set('key', 'value')
    result = await server.get('key')

    assert result == 'value'

    server.stop()


class SwappableProtocolTests(unittest.TestCase):

    def test_default_protocol(self):
        """
        An ordinary Server object will initially not have a protocol, but will
        have a KademliaProtocol object as its protocol after its listen()
        method is called.
        """
        loop = asyncio.get_event_loop()
        server = Server()
        self.assertIsNone(server.protocol)
        loop.run_until_complete(server.listen(8469))
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
        loop = asyncio.get_event_loop()
        server = Server()
        loop.run_until_complete(server.listen(8469))
        self.assertNotIsInstance(server.protocol, CoconutProtocol)
        server.stop()

        # ...but our custom server does.
        husk_server = HuskServer()
        loop.run_until_complete(husk_server.listen(8469))
        self.assertIsInstance(husk_server.protocol, CoconutProtocol)
        husk_server.stop()
