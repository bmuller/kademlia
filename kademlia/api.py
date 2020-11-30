from quart import Quart, jsonify, request
import asyncio
from keri.core.eventing import Kever, Signer, Serder, CryOneDex, Baser, Siger
import keri
import json

app = Quart(__name__)

node = None
storage = None

def run_api(kademlia_node, baser):
    global node
    node = kademlia_node
    storage = baser
    app.run(loop=asyncio.get_event_loop())

@app.route('/id/<aid>')
async def get_id_with_aid(aid):
    # accepts base64 Kevers
    # todo verify

    id = await node.get('evts.' + aid)
    if hasattr(id, 'decode'):
        return jsonify(id.decode())
    return jsonify(id)

# witness will have to send you a registration event.
@app.route('/id', methods=['POST'])
async def publish_aid_id_mapping():
    body_bytes = await request.get_data()
    body = None
    try:
        body = json.loads(body_bytes)
    except Exception as e:
        return jsonify(e)

    required_json_params = ["serder", "sigers"]
    for param in required_json_params:
        if param not in body:
            raise ValueError(f"request body missing required param {param}")

    serder = Serder(ked=body["serder"])
    if len(serder.ked["wits"]) < 1:
        raise ValueError(f"must provide at least one witness prefix")

    sg = Siger(qb64=body["sigers"][0]) # TODO support multiple sigers
    s = [Signer(qb64=sg.qb64)]
    # s = [Signer(raw=sg.raw, code=sg.code, transferable=True) for s in body["sigers"]]

    # do not use local Baser here because this might be stored remotely on another. Use a temp one only for verifying
    # TODO temporarily disabled, this line verifies the AID goes with the signature. Debug problem
    # TODO store kevers locally? Perhaps they only must exist remotely at destination node
    # kever = Kever(serder=serder, sigers=s, baser=Baser())

    # append db name to front with a dot so the backend knows which Baser db to store value in
    await node.set('evts.' + serder.ked["pre"], serder.ked["wits"][0])

    return jsonify("done")

@app.route('/ip/<witness_id>')
async def get_ip_with_id(witness_id):
    ip = await node.get('evts.' + witness_id)
    if hasattr(ip, 'decode'):
        return jsonify(ip.decode())
    return jsonify(ip)

@app.route('/ip', methods=['POST'])
async def publish_id_ip_mapping():
    # todo verify that the ip is signed by the witness and the witness_id is valid(?)
    # await node.set('evts.' + witness_id, witness_ip)
    return jsonify("temporarily not implemented until verification logic is correct")


