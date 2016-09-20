from mock import MagicMock, ANY

from spacel.security.kms_crypt import KmsCrypto
from spacel.security.password import PasswordManager
from spacel.security.payload import EncryptedPayload
from test import REGION
from test.security import BaseKmsTest

PASSWORD_LENGTH = 32
PASSWORD_NAME = 'test-password'


class TestPasswordManager(BaseKmsTest):
    def setUp(self):
        super(TestPasswordManager, self).setUp()
        self.dynamodb = MagicMock()
        self.clients.dynamodb.return_value = self.dynamodb
        self.kms_crypto = MagicMock(spec=KmsCrypto)
        self.password = PasswordManager(self.clients, self.kms_crypto)

    def test_generate_password(self):
        password = self.password._generate_password(PASSWORD_LENGTH)
        self.assertEquals(PASSWORD_LENGTH, len(password))

        other_password = self.password._generate_password(PASSWORD_LENGTH)
        self.assertNotEquals(password, other_password)

    def test_get_password_existing(self):
        self.dynamodb.get_item.return_value = {
            'Item': (EncryptedPayload('a', 'b', 'c', REGION, 'utf-8')
                     .dynamodb_item())
        }

        encrypted, decrypt_func = self.password.get_password(self.app, REGION,
                                                             PASSWORD_NAME)
        self.assertIsInstance(encrypted, EncryptedPayload)
        self.assertEquals(encrypted.iv, 'a')
        self.dynamodb.put_item.assert_not_called()
        self.kms_crypto.encrypt.assert_not_called()

        # Decrypt is deferred until absolutely necessary:
        self.kms_crypto.decrypt_payload.assert_not_called()
        decrypt_func()
        self.kms_crypto.decrypt_payload.assert_called_with(ANY)

    def test_get_password_generate(self):
        self.dynamodb.get_item.return_value = {}
        encrypted, decrypt_func = self.password.get_password(self.app, REGION,
                                                             PASSWORD_NAME)

        self.kms_crypto.encrypt.assert_called_with(self.app, REGION, ANY)
        self.dynamodb.put_item.assert_called_with(TableName=ANY,
                                                  Item=ANY,
                                                  ConditionExpression=ANY)

        # Decrypt is never called:
        decrypt_func()
        self.kms_crypto.decrypt_payload.assert_not_called()

    def test_decrypt(self):
        encrypted = MagicMock()
        self.password.decrypt(encrypted)
        self.kms_crypto.decrypt_payload.assert_called_with(encrypted)
