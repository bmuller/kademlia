import logging
import asyncio
import sys
sys.path.append("eqitii-dht")

from aiohttp import web
from kademlia.network import Server

KADEMLIA_PORT = 8468
API_PORT = 8080

loop = asyncio.get_event_loop()
server = 'global'
server = Server()
server.listen(KADEMLIA_PORT)

loop.set_debug(True)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

if len(sys.argv) == 2:
    bootstrap_node = (sys.argv[1], KADEMLIA_PORT)
    loop.run_until_complete(server.bootstrap([bootstrap_node]))


async def read_key(request):
    global server

    key = request.match_info.get('key')
    text = await server.get(key)
    if text:
        return web.Response(text=text)
    else:
        return web.Response(text='No such key')


async def set_key(request):
    global server

    key = request.match_info.get('key')
    data = await request.json()
    await server.set(key, str(data))
    return web.Response(text=str(data))


app = web.Application()
app.add_routes([web.get('/dht/{key}', read_key)])
app.add_routes([web.post('/dht/{key}', set_key)])

web.run_app(app, port=API_PORT)
