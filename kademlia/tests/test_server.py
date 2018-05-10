import asyncio
import unittest
import threading

from kademlia.network import Server
from kademlia.protocol import KademliaProtocol


class SwappableProtocolTests(unittest.TestCase):

    def test_custom_event_loop(self):
        custom_loop = asyncio.new_event_loop()
        server = Server()
        server.listen(8468)

        custom_loop = asyncio.new_event_loop()
        server2 = Server(custom_event_loop=custom_loop)

        server_thread = threading.Thread(
            target=setup_extra_server,
            args=[server2, custom_loop]
        )
        server_thread.start()
        # testing using the custom event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            server.bootstrap([("localhost", 8469)])
        )
        loop.run_until_complete(
            server.set("test", "test1")
        )
        rec_value = loop.run_until_complete(
            server.get("test")
        )
        server.stop()
        stop_extra_server(server2, custom_loop)

        server_thread.join()
        assert rec_value == "test1"

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


def setup_extra_server(server, custom_loop, port=8469):
    server.listen(port)
    custom_loop.run_forever()


def stop_extra_server(server, event_loop):
    server.stop()
    event_loop.call_soon_threadsafe(event_loop.stop)
