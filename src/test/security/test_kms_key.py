from botocore.exceptions import ClientError

from spacel.security.kms_key import KmsKeyFactory
from test import REGION
from test.security import BaseKmsTest, KEY_ARN, CLIENT_ERROR

ALIAS = 'alias/test-orbit-test-app'
KEY_METADATA = {
    'KeyMetadata': {
        'Arn': KEY_ARN,
        'Enabled': True
    }
}


class TestKmsKeyFactory(BaseKmsTest):
    def setUp(self):
        super(TestKmsKeyFactory, self).setUp()
        self.kms_factory = KmsKeyFactory(self.clients)

    def test_get_key_alias(self):
        alias = self.kms_factory.get_key_alias(self.app)
        self.assertEquals(ALIAS, alias)

    def test_get_key_exists(self):
        self.kms.describe_key.return_value = KEY_METADATA

        key = self.kms_factory.get_key(self.app, REGION)
        self.assertEquals(KEY_ARN, key)

        self.kms.describe_key.assert_called_with(KeyId=ALIAS)
        self.kms.create_key.assert_not_called()

    def test_get_key_exists_disabled(self):
        key_metadata = KEY_METADATA.copy()
        key_metadata['KeyMetadata']['Enabled'] = False
        self.kms.describe_key.return_value = key_metadata

        key = self.kms_factory.get_key(self.app, REGION)
        self.assertIsNone(key)

        self.kms.describe_key.assert_called_with(KeyId=ALIAS)

    def test_get_key_not_found(self):
        self.kms.describe_key.side_effect = ClientError({
            'Error': {
                'Message': 'Invalid keyId %s' % ALIAS
            }
        }, 'DescribeKey')

        self.kms_factory.get_key(self.app, REGION)

        # Key is created:
        self.kms.create_key.assert_called_once_with()

    def test_get_key_exception(self):
        self.kms.describe_key.side_effect = CLIENT_ERROR

        self.assertRaises(ClientError, self.kms_factory.get_key,
                          self.app, REGION)

    def test_create_key(self):
        self.kms.create_key.return_value = KEY_METADATA

        key = self.kms_factory.create_key(self.app, REGION)
        self.assertEquals(KEY_ARN, key)

        self.kms.describe_key.assert_not_called()
        self.kms.create_key.assert_called_once_with()
        self.kms.create_alias.assert_called_with(AliasName=ALIAS,
                                                 TargetKeyId=KEY_ARN)
        self.kms.schedule_key_deletion.assert_not_called()

    def test_create_key_exception(self):
        self.kms.create_key.return_value = KEY_METADATA
        self.kms.create_alias.side_effect = CLIENT_ERROR

        self.assertRaises(ClientError, self.kms_factory.create_key,
                          self.app, REGION)
        self.kms.schedule_key_deletion.assert_called_with(
            KeyId=KEY_ARN,
            PendingWindowInDays=7
        )
