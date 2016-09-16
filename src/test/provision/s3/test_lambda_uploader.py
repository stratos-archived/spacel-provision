from mock import MagicMock, ANY
import unittest
from spacel.aws import ClientCache
from spacel.provision.s3.lambda_uploader import LambdaUploader

BUCKET = 'bucket'
SAMPLE_SCRIPT = 'sns-to-slack.js'


class TestLambdaUploader(unittest.TestCase):
    def setUp(self):
        self.s3 = MagicMock()
        self.clients = MagicMock(spec=ClientCache)
        self.clients.s3.return_value = self.s3
        self.lambda_uploader = LambdaUploader(self.clients, 'us-west-2', BUCKET)

    def test_load_cache(self):
        self.lambda_uploader._load(SAMPLE_SCRIPT)
        self.lambda_uploader._load(SAMPLE_SCRIPT)

    def test_upload(self):
        self.lambda_uploader.upload(SAMPLE_SCRIPT, {
            '__FOO__': 'bar'
        })

        self.s3.Object.assert_called_with(BUCKET, ANY)
