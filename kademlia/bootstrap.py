import logging
import asyncio
from kademlia.const import *
from kademlia.network import Server
from kademlia.storage import KeriStorage
from keri.db.dbing import Baser

def setup_logging():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log = logging.getLogger('kademlia')
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)


setup_logging()

loop = asyncio.get_event_loop()
loop.set_debug(True)

storage = KeriStorage(Baser())
server = Server(storage=storage)
loop.run_until_complete(server.listen(bootstrap_port))

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    server.stop()
    loop.close()
