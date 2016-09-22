from botocore.exceptions import ClientError
from mock import MagicMock

from spacel.aws import ClientCache
from test import BaseSpaceAppTest

PLAINTEXT_KEY = '0000000000000000'
ENCRYPTED_KEY = 'topsecret'

KEY_ARN = ('arn:aws:kms:us-west-2:111111111111111:key/' +
           '1111111-222222-33333-44444-55555555')

CLIENT_ERROR = ClientError({'Error': {'Message': 'Kaboom'}}, 'DescribeKey')


class BaseKmsTest(BaseSpaceAppTest):
    def setUp(self):
        super(BaseKmsTest, self).setUp()
        self.kms = MagicMock()
        self.kms.generate_data_key.return_value = {
            'Plaintext': PLAINTEXT_KEY,
            'CiphertextBlob': ENCRYPTED_KEY
        }
        self.kms.decrypt.return_value = {
            'Plaintext': PLAINTEXT_KEY
        }

        self.clients = MagicMock(spec=ClientCache)
        self.clients.kms.return_value = self.kms
