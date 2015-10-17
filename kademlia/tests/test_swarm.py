import time
import random
import threading
import unittest
from twisted.internet import reactor
from kademlia.network import Server


TEST_SWARM_SIZE = 20


class TestSwarm(unittest.TestCase):

    def setUp(self):

        # create peers
        self.swarm = []
        for i in range(TEST_SWARM_SIZE):
            print("creating peer {0}".format(i))
            peer = Server()
            bootstrap_peers = [
                ("127.0.0.1", 8468 + x) for x in range(i)
            ][-1:]  # each peer only knows of the last peer
            peer.bootstrap(bootstrap_peers)
            peer.listen(8468 + i)
            self.swarm.append(peer)
        
        # start reactor
        self.reactor_thread = threading.Thread(
            target=reactor.run, kwargs={"installSignalHandlers": False}
        )
        self.reactor_thread.start()
        time.sleep(12)  # wait until they organize

    def tearDown(self):
        reactor.stop()
        self.reactor_thread.join()

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
                finished.set()
            random_peer.set(key, value).addCallback(callback)
            finished.wait()  # block until added

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
            random_peer.get(key).addCallback(callback)
            finished.wait()  # block until found
        self.assertEqual(inserted, found)


if __name__ == "__main__":
    unittest.main()
