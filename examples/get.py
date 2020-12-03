import logging
import asyncio
import sys

from kademlia.network import Server

# if len(sys.argv) != 4:
#     print("Usage: python get.py <bootstrap node> <bootstrap port> <key>")
#     sys.exit(1)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

async def run():
    server = Server()
    await server.listen(8469)
    bootstrap_node = ("127.0.0.1", 8468)
    await server.bootstrap([bootstrap_node])

    result = await server.get("test_key")
    print("Get result:", result)
    # server.stop()

asyncio.run(run())
