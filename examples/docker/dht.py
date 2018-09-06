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

server = Server()
server.listen(8468)

loop = asyncio.get_event_loop()
loop.set_debug(True)

if len(sys.argv) == 2:
    bootstrap_node = (sys.argv[1], 8468)
    loop.run_until_complete(server.bootstrap([bootstrap_node]))

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    server.stop()
    loop.close()
