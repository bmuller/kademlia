import logging
import asyncio
import time

from kademlia.network import Server
import threading

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()

def main_server():
    server = Server()

    loop.set_debug(True)
    loop.run_until_complete(server.listen(8468))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


threading.Thread(target=main_server).start()

time.sleep(5)


async def run_set():
    server = Server()
    await server.listen(8470)
    bootstrap_node = ("127.0.0.1", 8468)
    await server.bootstrap([bootstrap_node])
    await server.set("test_key", "Hello")
    while True:
        pass
    # server.stop()


def run_async_set():
    asyncio.run(run_set())


threading.Thread(target=run_async_set).start()
time.sleep(3)


async def run_get():
    server = Server()
    await server.listen(8469)
    bootstrap_node = ("127.0.0.1", 8468)
    await server.bootstrap([bootstrap_node])

    result = await server.get("test_key")
    print("Get result:", result)
    # server.stop()


def run_async_get():
    asyncio.run(run_get())


threading.Thread(target=run_async_get).start()
