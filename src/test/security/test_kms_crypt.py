import six
from botocore.exceptions import ClientError
from mock import MagicMock

from spacel.security.kms_crypt import KmsCrypto
from spacel.security.kms_key import KmsKeyFactory
from test import ORBIT_REGION
from test.security import BaseKmsTest, PLAINTEXT_KEY, ENCRYPTED_KEY


class TestKmsCrypto(BaseKmsTest):
    def setUp(self):
        super(TestKmsCrypto, self).setUp()
        self.kms_key = MagicMock(spec=KmsKeyFactory)
        self.kms_crypt = KmsCrypto(self.clients, self.kms_key)

    def test_roundtrip_bytes(self):
        self._round_trip(six.b('hello world'))

    def test_roundtrip_ascii(self):
        self._round_trip('hello world')

    def test_roundtrip_utf8(self):
        self._round_trip(six.u('\u9731'))

    def test_decrypt_invalid(self):
        # Invalid ciphertext: decrypts to garbage
        self.assertRaises(ValueError, self.kms_crypt.decrypt,
                          b'1234567890123456',
                          b'1234567890123456',
                          b'1234567890123456',
                          ORBIT_REGION,
                          'bytes')

    def test_encrypt_missing_key(self):
        # GenerateDataKey fails as key doesn't exist, key is created:
        key_not_found = ClientError({'Error': {
            'Message': ('An error occurred (NotFoundException) when calling ' +
                        'the GenerateDataKey operation: Alias ' +
                        'arn:aws:kms:us-east-1:330658367937:alias/your-alias ' +
                        'is not found')
        }}, 'GenerateDataKey')
        self.kms.generate_data_key.side_effect = [
            key_not_found,
            {
                'Plaintext': PLAINTEXT_KEY,
                'CiphertextBlob': ENCRYPTED_KEY
            }
        ]

        self.kms_crypt.encrypt(self.app_region, 'test')

        self.assertEquals(2, self.kms.generate_data_key.call_count)
        self.kms_key.create_key.assert_called_with(self.app_region)

    def test_encrypt_error(self):
        # GenerateDataKey fails as key doesn't exist, key is created:
        key_not_found = ClientError({'Error': {
            'Message': 'Kaboom'
        }}, 'GenerateDataKey')
        self.kms.generate_data_key.side_effect = key_not_found
        self.assertRaises(ClientError, self.kms_crypt.encrypt, self.app_region,
                          'test')

    def _round_trip(self, data):
        item = self.kms_crypt.encrypt(self.app_region, data)
        self.assertEquals(ENCRYPTED_KEY, item.key)
        self.assertEquals(ORBIT_REGION, item.key_region)

        decrypted = self.kms_crypt.decrypt_payload(item)
        self.assertEquals(decrypted, data)

        self.kms_key.create_key.assert_not_called()
