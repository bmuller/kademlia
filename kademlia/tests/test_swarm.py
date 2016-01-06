import time
# import signal
import random
import threading
from twisted.trial import unittest
from kademlia.network import Server


PORT = 8468
TEST_SWARM_SIZE = 20


# FIXME figure out why this test doesnt work!!!


@unittest.SkipTest
class TestSwarm(unittest.TestCase):

    def setUp(self):

        # create peers
        self.swarm = []
        for i in range(TEST_SWARM_SIZE):
            peer = Server()
            bootstrap_peers = [
                ("127.0.0.1", PORT + x) for x in range(i)
            ][-1:]  # each peer only knows of the last peer
            peer.bootstrap(bootstrap_peers)
            peer.listen(PORT + i)
            self.swarm.append(peer)

        # stabalize network overlay
        time.sleep(10)
        for peer in self.swarm:
            peer.bootstrap(peer.bootstrappableNeighbors())
        time.sleep(10)
        for peer in self.swarm:
            peer.bootstrap(peer.bootstrappableNeighbors())
        time.sleep(10)

    def test_swarm(self):
        inserted = dict([
            ("key_{0}".format(i), "value_{0}".format(i)) for i in range(5)
        ])
        inserted_items = inserted.items()

        # insert randomly into the swarm
        random.shuffle(inserted_items)
        for key, value in inserted_items:
            print("inserting {0} -> {1}".format(key, value))
            random_peer = random.choice(self.swarm)
            finished = threading.Event()

            def callback(result):
                self.assertTrue(result)
                finished.set()
            random_peer.set(key, value).addCallback(callback)
            finished.wait(timeout=10)  # block until added
            self.assertTrue(finished.isSet())

        # retrieve values randomly
        found = {}
        random.shuffle(inserted_items)
        for key, inserted_value in inserted_items:
            random_peer = random.choice(self.swarm)
            finished = threading.Event()

            def callback(found_value):
                print("found {0} -> {1}".format(key, found_value))
                found[key] = found_value
                finished.set()
                self.assertTrue(found_value is not None)
            random_peer.get(key).addCallback(callback)
            finished.wait(timeout=10)  # block until found
            self.assertTrue(finished.isSet())

        self.assertEqual(inserted, found)
