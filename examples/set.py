import logging
import asyncio
import sys

from kademlia.network import Server

if len(sys.argv) != 3:
    print("Usage: python set.py <key> <value>")
    sys.exit(1)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
server.listen(8469)
loop.run_until_complete(server.bootstrap([("127.0.0.1", 8468)]))
loop.run_until_complete(server.set(sys.argv[1], sys.argv[2]))
server.stop()
loop.close()
