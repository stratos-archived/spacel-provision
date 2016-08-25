from mock import MagicMock, ANY
import unittest
from spacel.provision.lambda_s3 import LambdaUploader

BUCKET = 'bucket'
SAMPLE_SCRIPT = 'sns-to-slack.js'


class TestLambdaUploader(unittest.TestCase):
    def setUp(self):
        self.s3 = MagicMock()

        self.lambda_uploader = LambdaUploader(self.s3, BUCKET)

    def test_load_cache(self):
        self.lambda_uploader._load(SAMPLE_SCRIPT)
        self.lambda_uploader._load(SAMPLE_SCRIPT)

    def test_upload(self):
        self.lambda_uploader.upload(SAMPLE_SCRIPT, {
            '__FOO__': 'bar'
        })

        self.s3.Object.assert_called_with(BUCKET, ANY)
