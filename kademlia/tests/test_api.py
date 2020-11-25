import nest_asyncio
import pytest
import kademlia.network
from kademlia import api
from kademlia.const import *
from kademlia.generate_aid import gen_nontransferable_serialized_aid, gen_serialized_aid

# integration tests - these require bootstrap.py to be running

@pytest.mark.asyncio
async def test_api():
    tc = await setup_test_client()

    witness_id = gen_nontransferable_serialized_aid()
    aid = gen_serialized_aid([witness_id])
    # TODO witness_aid.sign_ip("1.2.3.4") when implemented
    witness_ip = "signed_ip1"

    await publish_then_get_id_from_aid(tc, aid, witness_id)
    # await publish_then_get_ip_from_id(tc, witness_id, witness_ip)


async def publish_then_get_id_from_aid(tc, aid, id):
    response = await tc.post(f'/id/{aid}/{id}', json=None)
    assert response.status_code == 200
    result = await response.get_json()
    assert result == "done"

    response = await tc.get(f'/id/{aid}', json=None)
    assert response.status_code == 200
    result = await response.get_json()
    assert result == id

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

