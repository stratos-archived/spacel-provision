import unittest
from mock import MagicMock

from spacel.aws import ClientCache
from spacel.provision.s3.template_uploader import TemplateUploader

REGION = 'us-west-2'


class TestTemplateUploader(unittest.TestCase):
    def setUp(self):
        self.clients = MagicMock(spec=ClientCache)
        self.template = TemplateUploader(self.clients, REGION, '')
        self.template._upload = MagicMock()

    def test_upload(self):
        self.template.upload('{}', 'foo')
        self.template._upload.assert_called_with(
            'foo/bf21a9e8fbc5a3846fb05b4fa0859e0917b2202f.template',
            '{}')
