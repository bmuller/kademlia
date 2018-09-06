import logging
import asyncio
import sys
sys.path.append("eqitii-dht")

from kademlia.network import Server

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
bootstrap_node = (sys.argv[1], 8468)
loop.run_until_complete(server.bootstrap([bootstrap_node]))
loop.run_until_complete(server.set(sys.argv[2], sys.argv[3]))
server.stop()
loop.close()
