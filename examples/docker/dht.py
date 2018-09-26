import logging
import asyncio
import json
import sys
import ast

sys.path.append("eqitii-dht")

from aiohttp import web
from kademlia.network import Server

KADEMLIA_PORT = 8468
API_PORT = 8080
KEY_ABSENT_MESSAGE = 'No such key'
NO_KEYS = 'No keys'

loop = asyncio.get_event_loop()
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
    try:
        text = await server.get(key)
    except:
        raise web.HTTPInternalServerError()
    if text:
        return web.Response(text=text)
    else:
        return web.Response(text=KEY_ABSENT_MESSAGE)


async def set_key(request):
    global server

    key = request.match_info.get('key')
    try:
        data = await request.json()
        await server.set(key, json.dumps(data))
        keys = await server.get('keys')
        if not keys:
            keys = []
        else:
            keys = ast.literal_eval(keys)
        if not key in keys:
            keys.append(key)
            await server.set('keys', str(keys))
    except:
        raise web.HTTPInternalServerError()
    return web.Response(text=str(data))


async def read_all(request):
    global server

    try:
        keys = await server.get('keys')
        if not keys:
            return web.Response(text=NO_KEYS)
        result = {}
        keys = ast.literal_eval(keys)
        for key in keys:
            value = await server.get(key)
            result[key] = json.loads(value)
        return web.Response(text=json.dumps(result))
    except:
        raise web.HTTPInternalServerError()


async def read_all_list(request):
    global server

    try:
        keys = await server.get('keys')
        if not keys:
            return web.Response(text=NO_KEYS)
        result = []
        keys = ast.literal_eval(keys)
        for key in keys:
            obj = {"key": key}
            value = await server.get(key)
            obj["value"] = json.loads(value)
            result.append(obj)
        return web.Response(text=json.dumps(result))
    except:
        raise web.HTTPInternalServerError()


app = web.Application()
app.add_routes([web.get('/dht/all', read_all)])
app.add_routes([web.get('/dht/all_list', read_all_list)])
app.add_routes([web.get('/dht/{key}', read_key)])
app.add_routes([web.post('/dht/{key}', set_key)])

web.run_app(app, port=API_PORT)
