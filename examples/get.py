import logging
import asyncio
import sys

from kademlia.network import Server

if len(sys.argv) != 2:
    print("Usage: python get.py <key>")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
server.listen(8469)
loop.run_until_complete(server.bootstrap([("127.0.0.1", 8468)]))
result = loop.run_until_complete(server.get(sys.argv[1]))
server.stop()
loop.close()

print("Get result:", result)
