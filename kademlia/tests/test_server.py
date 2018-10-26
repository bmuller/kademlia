import unittest
from kademlia.dto.dto import Value
import json
from kademlia.utils import validate_authorization, check_new_value_valid
from unittest.mock import Mock, patch
import asyncio

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



class ServerTests(unittest.TestCase):

    @patch('kademlia.network.check_new_value_valid')
    @patch('kademlia.network.validate_authorization')
    def test_set_auth(self, mocked_va, mocked_cnvv):
        """
        set_auth should validate value, check authorization and save value to the network
        """
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)


        async def run_test():
            server = Server()

            def async_return(result):
                f = asyncio.Future()
                f.set_result(result)
                return f

            server.get = Mock(return_value=async_return(None))
            server.set = Mock(return_value=async_return(True))
            value = Mock()
            value.authorization = None
            await server.set_auth('test key', value)
            server.get.assert_called_with('test key')

            value.authorization = 'auth'
            await server.set_auth('test key', value)
            mocked_va.assert_called_with(b'\xb2\x95\x8d\x18Pbw"`\xc3\xfa\x82\xcce\x1e\x12mT\xb2h', value)

            server.get = Mock(return_value=async_return('some value'))
            json.loads = Mock(return_value='json')
            Value.of_json = Mock(return_value='stored value')
            await server.set_auth('test key', value)
            json.loads.assert_called_with('some value')
            Value.of_json.assert_called_with('json')
            mocked_cnvv.assert_called_with(b'\xb2\x95\x8d\x18Pbw"`\xc3\xfa\x82\xcce\x1e\x12mT\xb2h', 'stored value', value)

            server.stop()

        coro = asyncio.coroutine(run_test)
        event_loop.run_until_complete(coro())