import unittest
from mock import MagicMock

from spacel.aws import ClientCache
from spacel.provision.s3.base import BaseUploader

REGION = 'us-east-1'


class TestBaseUploader(unittest.TestCase):
    def setUp(self):
        self.clients = MagicMock(spec=ClientCache)
        self.base = BaseUploader(self.clients, REGION, '')

    def test_hash_helper(self):
        test_hash = self.base._hash('test')
        self.assertEquals('a94a8fe5ccb19ba61c4c0873d391e987982fbbd3', test_hash)

    def test_upload_helper(self):
        path = 'foo/bf21a9e8fbc5a3846fb05b4fa0859e0917b2202f.template'
        self.base._upload(path, '')
        self.clients.s3.assert_called_with(REGION)
