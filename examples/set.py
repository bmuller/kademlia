import asyncio
import logging
import sys

from kademlia.network import Server

if len(sys.argv) != 5:
    print("Usage: python set.py <bootstrap node> <bootstrap port> <key> <value>")
    sys.exit(1)

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
log = logging.getLogger("kademlia")
log.addHandler(handler)
log.setLevel(logging.DEBUG)


async def run():
    server = Server()
    await server.listen(8469)
    bootstrap_node = (sys.argv[1], int(sys.argv[2]))
    await server.bootstrap([bootstrap_node])
    await server.set(sys.argv[3], sys.argv[4])
    server.stop()


asyncio.run(run())
