import logging
import asyncio
import sys

from kademlia.network import Server

# if len(sys.argv) != 5:
#     print("Usage: python set.py <bootstrap node> <bootstrap port> <key> <value>")
#     sys.exit(1)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

async def run():
    server = Server()
    await server.listen(8470)
    bootstrap_node = ("127.0.0.1", 8468)
    await server.bootstrap([bootstrap_node])
    await server.set("test_key", "Hello")
    while True:
        pass
    # server.stop()

asyncio.run(run())
