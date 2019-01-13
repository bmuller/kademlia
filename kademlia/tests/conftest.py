import pytest

from kademlia.storage import DiskStorage
from kademlia.network import Server


@pytest.yield_fixture
def bootstrap_node(event_loop):
    server = Server()
    event_loop.run_until_complete(server.listen(8468))

    try:
        yield ('127.0.0.1', 8468)
    finally:
        server.stop()


@pytest.yield_fixture()
def disk_storage(tmpdir):
    filename = tmpdir.join('kademlia.db')
    try:
        yield DiskStorage(filename=str(filename))
    finally:
        filename.remove()
