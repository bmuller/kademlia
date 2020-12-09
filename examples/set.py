import logging
import asyncio

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)


def run():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    server = Server()
    loop.run_until_complete(server.listen(8470))
    bootstrap_node = ("127.0.0.1", 8468)
    loop.run_until_complete(server.bootstrap(bootstrap_node))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


run()
