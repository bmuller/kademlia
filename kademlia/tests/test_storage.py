import unittest
import time
import pickledb
from unittest.mock import Mock, patch

from kademlia.network import Server
from kademlia.storage import ForgetfulStorage
from kademlia.storage import DiskStorage


class ForgetfulStorageTests(unittest.TestCase):

    def setUp(self):
        self.ts = ForgetfulStorage()

    @patch('kademlia.storage.time')
    def test___setitem_(self, mocked_time):
        """
        __setitem__ should set value to storage and add timestamp
        __setitem__ should call cull method
        """
        mocked_time.monotonic = Mock(return_value=1)
        self.ts.cull = Mock()
        self.ts['key1'] = 'value1'
        self.assertEqual(self.ts.data['key1'], (1, 'value1'))
        self.assertTrue(self.ts.cull.called)

    def test_cull(self):
        """
        cull should remove items older then ttl from storage
        """
        self.ts.iteritemsOlderThan = Mock(return_value=[('key1', 'value1')])
        self.ts.data['key1'] = (1, 'value1')
        self.ts.data['key2'] = (2, 'value2')
        self.ts.cull()
        self.assertTupleEqual(self.ts.data['key2'], (2, 'value2'))
        with self.assertRaises(KeyError):
            self.ts.data['key1']

    def test_get(self):
        """
        Get should get value from storage or return dafault value
        Get should call cull method
        """
        self.ts.cull = Mock()
        self.ts['key1'] = 'value1'
        self.assertEqual(self.ts.get('key1'), 'value1')
        self.assertTrue(self.ts.cull.called)
        self.assertIsNone(self.ts.get('key2'))
        self.assertEqual(self.ts.get('key2', 'value2'), 'value2')
        self.assertEqual(self.ts.get('key1', 'value2'), 'value1')

    def test___getitem__(self):
        """
        Get should get value from storage or raise exception
        Get should call cull method
        """
        self.ts.cull = Mock()
        self.ts['key1'] = 'value1'
        self.assertEqual(self.ts['key1'], 'value1')
        self.assertTrue(self.ts.cull.called)
        with self.assertRaises(KeyError):
            self.ts['key2']

    @patch('kademlia.storage.time')
    def test_iteritemsOlderThan(self, mocked_time):
        """
        iteritemsOlderThan should return tuples with keys and values
        from storage for items not older than specified value
        """
        self.ts.cull = Mock()
        mocked_time.monotonic = Mock(side_effect=[1, 2, 3, 4])
        self.ts['key1'] = 'value1'
        self.ts['key2'] = 'value2'
        self.ts['key3'] = 'value3'
        self.assertEqual(len(self.ts.iteritemsOlderThan(2)), 2)


class DiskStorageTests(unittest.TestCase):

    def setUp(self):
        pickledb.load = Mock()
        self.ts = DiskStorage()

    @patch('kademlia.storage.time')
    def test___setitem_(self, mocked_time):
        """
        __setitem__ should set hex key to storage with timestamp and value
        __setitem__ should call dupm
        """
        mocked_time.time = Mock(return_value=123)
        self.ts.data.set = Mock()
        self.ts.data.dump = Mock()
        key = bytes.fromhex('91ecb5')
        self.ts[key] = 'value1'
        self.ts.data.set.assert_called_with('91ecb5', (123, 'value1'))
        self.ts.data.dump.assert_called_once()

    def test_get(self):
        """
        Get should get value from storage or return dafault value
        """
        self.ts.data.get = Mock(
            side_effect=[(1, 'value1'), None, None, (1, 'value1')])
        self.assertEqual(self.ts.get(bytes.fromhex('91ecb5')), 'value1')
        self.assertIsNone(self.ts.get(bytes.fromhex('91ecb6')))
        self.assertEqual(self.ts.get(
            bytes.fromhex('91ecb6'), 'value2'), 'value2')
        self.assertEqual(self.ts.get(
            bytes.fromhex('91ecb5'), 'value2'), 'value1')

    def test___getitem__(self):
        """
        Get should get value from storage
        """
        self.ts.data.get = Mock(return_value=(1, 'value1'))
        self.assertEqual(self.ts[bytes.fromhex('91ecb5')], 'value1')

    @patch('kademlia.storage.time')
    def test_iteritemsOlderThan(self, mocked_time):
        """
        iteritemsOlderThan should return tuples with keys and values
        from storage for items not older than specified value
        """
        mocked_time.time = Mock(return_value=4)
        self.ts.data.getall = Mock(return_value=('91ecb5', '91ecb6', '91ecb7'))
        self.ts.getAllValues = Mock(return_value=[(1, '91ecb5'), (2, '91ecb6'), (3, '91ecb7')])
        self.assertEqual(len(self.ts.iteritemsOlderThan(2)), 2)

    def test_getAllKeysBytes(self):
        """
        getAllKeysBytes should return list of keys in bytes format
        """
        self.ts.data.getall = Mock(return_value=('91ecb5', '91ecb6', '91ecb7'))
        self.assertEqual(self.ts.getAllKeysBytes(), [b'\x91\xec\xb5', b'\x91\xec\xb6', b'\x91\xec\xb7'])