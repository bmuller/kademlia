import unittest

from kademlia.storage import ForgetfulStorage


class ForgetfulStorageTest(unittest.TestCase):
    def test_storing(self):
        storage = ForgetfulStorage(10)
        storage['one'] = 'two'
        self.assertEqual(storage['one'], 'two')

    def test_forgetting(self):
        storage = ForgetfulStorage(0)
        storage['one'] = 'two'
        self.assertEqual(storage.get('one'), None)

    def test_iter(self):
        storage = ForgetfulStorage(10)
        storage['one'] = 'two'
        for key, value in storage:
            self.assertEqual(key, 'one')
            self.assertEqual(value, 'two')

    def test_iter_old(self):
        storage = ForgetfulStorage(10)
        storage['one'] = 'two'
        for key, value in storage.iter_older_than(0):
            self.assertEqual(key, 'one')
            self.assertEqual(value, 'two')


class TestDickStorage:
    def test_storing(self, disk_storage):  # pylint: disable=no-self-use
        storage = disk_storage
        storage['one'] = 'two'
        assert storage['one'] == 'two'

    def test_iter(self, disk_storage):  # pylint: disable=no-self-use
        storage = disk_storage
        storage['one'] = 'two'
        for key, value in storage:
            assert key == 'one'
            assert value == 'two'

    def test_iter_old(self, disk_storage):  # pylint: disable=no-self-use
        storage = disk_storage
        storage['one'] = 'two'
        for key, value in storage.iter_older_than(0):
            assert key == 'one'
            assert value == 'two'
