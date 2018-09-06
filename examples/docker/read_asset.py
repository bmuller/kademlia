import asyncio
import sys
sys.path.append("eqitii-dht")

from kademlia.network import Server

loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
server.listen(8469)
bootstrap_node = (sys.argv[1], 8468)
loop.run_until_complete(server.bootstrap([bootstrap_node]))
result = loop.run_until_complete(server.get(sys.argv[2]))
print(result)
server.stop()
loop.close()
