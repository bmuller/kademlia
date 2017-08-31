import logging
import asyncio

from kademlia.network import Server


logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
server.listen(8468)

def done(result):
    print("Key result:", result)

def setDone(result, server):
    server.get("a key").addCallback(done)

def bootstrapDone(found, server):
    server.set("a key", "a value").addCallback(setDone, server)

#server.bootstrap([("1.2.3.4", 8468)]).addCallback(bootstrapDone, server)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    server.stop()
    loop.close()
