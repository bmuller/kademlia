import nest_asyncio
import pytest
import kademlia.network
from kademlia import api
from kademlia.const import *
from kademlia.generate_aid import gen_nontransferable_serialized_aid, gen_serialized_aid
import json

# integration tests - these require bootstrap.py to be running
# TODO proper unit tests and move these to a better spot for integration tests
# TODO proper teardown; use clean db and wipe when done

@pytest.mark.asyncio
async def test_api():
    tc = await setup_test_client()

    # unnecessary to produce new one if using json example file
    # witness_id = gen_nontransferable_serialized_aid()
    # aid = gen_serialized_aid([witness_id])
    # TODO witness_aid.sign_ip("1.2.3.4") when implemented
    witness_ip = "signed_ip1"

    await publish_then_get_id_from_aid(tc)
    # TODO enable once verification works
    # await publish_then_get_ip_from_id(tc, witness_id, witness_ip)


async def publish_then_get_id_from_aid(tc):
    json_request = None
    with open('kademlia/tests/publish_aid_id_example.json') as f:
        json_request = json.load(f)

    response = await tc.post(f'/id', json=json_request)
    # this could be failing because the versionage vs is not the first element in the json
    # after it has been processed by the test client above, and it seems Keri cannot read it
    # if so. Posting the same request with Postman and the primary api works fine
    result = await response.get_json()
    assert result == "done"
    assert response.status_code == 200

    response = await tc.get(f'/id/{json_request["pre"]}', json=None)
    assert response.status_code == 200
    result = await response.get_json()
    assert result == json_request["wits"][0]

async def publish_then_get_ip_from_id(tc, id, ip):
    response = await tc.post(f'/ip/{id}/{ip}', json=None)
    assert response.status_code == 200
    result = await response.get_json()
    assert result == "done"

    response = await tc.get(f'/ip/{id}', json=None)
    assert response.status_code == 200
    result = await response.get_json()
    assert result == ip


# sets up a kademlia connection and test api client for integrated testing
async def setup_test_client():
    nest_asyncio.apply()
    node = kademlia.network.Server()
    await node.listen(primary_port)
    await node.bootstrap([("0.0.0.0", bootstrap_port)])
    api.node = node
    return api.app.test_client()

