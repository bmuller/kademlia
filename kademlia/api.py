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



# every entry in the dht should be signed

    # non tarnsferrable identifiers are trivial to verify (witness ip)
# more complicated when using transferable id cause you don't know current key state unless you process key event log



# register key event log or key state. in either case you provdie
# eventing.py in keripy Kever (event verification). attributes maintain the key state.


# Baser() database wraps the lmdb database. if you look in the db module in keri, there's a base class called lmdber and sublass called baser that maintains all tables.

# every identifier has its own kever (current key state) but all share one baser database to track key event logs.

# if kevers were stored on disk, someone could corrupt them on disk. Instead they're in memory and on bootup. you would replay


# event sourcing - can recreate any state at any time in past by replaying a log of events. it allows you to utilize horizontal scalability. normally difficult to track global state
# but DBs can't go back in time. event sourcing

# init processes inception event

# update method for all events after inception event.



# kever for every transferable id in database


# if nontransferable, kever is trivial as you only have inception event, and all you need is public key. could just write utility function to verify it


# needs a kever for everything

# just need the last establishment event and events since then. you never reference anything earlier than that when verifying state unless you want to replay the whole thing for ultimate trust

# each node is essentially a watcher. could create subclass of kever with additional attributes with whatever you are discovering about identifier. (like IP address attribute)

# merkle tree of all events in event log, keep key event state

#demo_sam.py runs a watcher in direct mode does what we want to add to keri.



# habitat keeps track of stuff coroutines need to share. shared memory

# a doer is a couratine runner

# setup creates a bunch of coroutines and run runs it


# async in python - with coroutine, code is linear again. when you need to wait for something you yield. you don't use


# two ways to use coroutine. 1 is pipes wehere one sends data to another. that is tightly coupled.
# loosely coupled is you use buffers instead. only use send for scheduling info.

# tyme is articficial time

#asyncio event loop is unordered, you can't reproduce things in control scheduling when you need tight schedulings.
# in coroutines they can be ordered (not depending on it in demo examples)

# chit is receipt

# one is watcher process and one is kademlia and they use shared memory interface like que queue to get between them

# make sure watcher verifies everything sent (both AIDs in cname)
# someone who uses discovery protocol also verifies on use. you don't want to have to trust a node. 0 trust is , never trust, always verify

# don't just send me the ip address, also send signed registration statement with verification necessary.

# ifyou're a watcher and i trust you then i ask for key event state, tehn you the watcher sign it and I can verify your signature and can verify that
# if I don't trust you, i ask for key event log so I can verify everything

# if ip address, I send back ip address mapping and registration mapping with signature with registrant prefix, just need this: ilk, ip address, signature from witness

# key event state you must sign

# request IP address message. I need to create schema with ilk 3 char and send design to Sam Smith
#


# create another table in the baser for IP registration messages. DHT 1) manages address space, each node has data

# don't store something unless it's been verified. can't cache something unverified


# modify kademlia class backend to use Baser db.

#LMDB  fastest memory mapped persistent DB of any merit (stable, security, mature, users in prod, available in all languages) (used by LDAP)



# terminology in programming. 1. java approach . name is flying birdcage. (very descriptive, very long) .   or use aviery (shorter but not well known). go look it up.
# 2.
# www.learnthat.org/suffixes (or something similar) turns noun into state, brew verb, brewery - place, brewer - person who brews


# all modules end in -ing. packages have descriptive name. in python standard library, lots of modules do that (logging)