from kademlia.storage import ForgetfulStorage


class ForgetfulStorageTest:
    def test_storing(self):
        storage = ForgetfulStorage(10)
        storage["one"] = "two"
        assert storage["one"] == "two"

    def test_forgetting(self):
        storage = ForgetfulStorage(0)
        storage["one"] = "two"
        assert storage.get("one") is None

    def test_iter(self):
        storage = ForgetfulStorage(10)
        storage["one"] = "two"
        for key, value in storage:
            assert key == "one"
            assert value == "two"

    def test_iter_old(self):
        storage = ForgetfulStorage(10)
        storage["one"] = "two"
        for key, value in storage.iter_older_than(0):
            assert key == "one"
            assert value == "two"
