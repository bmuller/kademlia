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
