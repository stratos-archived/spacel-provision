import logging

from mock import patch, ANY, MagicMock
from six import BytesIO

from spacel.cli.secret import (handle_secret, get_plaintext, encrypt,
                               update_manifest)
from test import BaseSpaceAppTest, ORBIT_NAME, APP_NAME, ORBIT_REGION
from test.security.test_payload import ENCRYPTED_PAYLOAD

TEST_KEY = 'test-key'


class TestSecretCommand(BaseSpaceAppTest):
    def tearDown(self):
        logger = logging.getLogger()
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    def test_handle_secret_no_value(self):
        handled = handle_secret(ORBIT_NAME, APP_NAME, [ORBIT_REGION], False,
                                False, None, None, 'CRITICAL',
                                BytesIO())
        self.assertFalse(handled)

    def test_handle_secret_no_regions(self):
        handled = handle_secret(ORBIT_NAME, APP_NAME, [], False,
                                False, TEST_KEY, 'test-value', 'CRITICAL',
                                BytesIO())
        self.assertFalse(handled)

    @patch('spacel.cli.secret.encrypt')
    def test_handle_secret_encrypt_failed(self, mock_encrypt):
        mock_encrypt.return_value = None
        handled = handle_secret(ORBIT_NAME, APP_NAME, [ORBIT_REGION], False,
                                False, TEST_KEY, 'test-value', 'CRITICAL',
                                BytesIO())
        self.assertFalse(handled)

    @patch('spacel.cli.secret.encrypt')
    @patch('spacel.cli.secret.update_manifest')
    def test_handle_secret(self, mock_update, mock_encrypt, ):
        mock_encrypt.return_value = {ORBIT_REGION: ENCRYPTED_PAYLOAD}
        handled = handle_secret(ORBIT_NAME, APP_NAME, [ORBIT_REGION], False,
                                False, TEST_KEY, 'test-value', 'CRITICAL',
                                BytesIO())
        mock_update.assert_not_called()
        self.assertTrue(handled)

    @patch('spacel.cli.secret.encrypt')
    @patch('spacel.cli.secret.update_manifest')
    def test_handle_secret_modify(self, mock_update, mock_encrypt):
        mock_encrypt.return_value = {ORBIT_REGION: ENCRYPTED_PAYLOAD}
        handled = handle_secret(ORBIT_NAME, APP_NAME, [ORBIT_REGION], False,
                                True, TEST_KEY, 'test-value', 'CRITICAL',
                                BytesIO())
        mock_update.assert_called_once_with(ANY, ANY, TEST_KEY, ANY)
        self.assertTrue(handled)

    def test_get_plaintext_stream(self):
        buffer = BytesIO(b'test')
        plaintext = get_plaintext(TEST_KEY, '-', buffer)
        self.assertEquals(b'test', plaintext)

    def test_get_plaintext_key_value(self):
        plaintext = get_plaintext(TEST_KEY, 'value', None)
        self.assertEquals('test-key=value', plaintext)

    def test_get_plaintext_value(self):
        plaintext = get_plaintext(None, 'value', None)
        self.assertEquals('value', plaintext)

    @patch('spacel.cli.secret.KmsCrypto')
    def test_encrypt_error(self, kms_crypto_factory):
        kms_crypto = MagicMock()
        kms_crypto.encrypt.side_effect = self._client_error()
        kms_crypto_factory.return_value = kms_crypto
        ciphertexts = encrypt(self.app, 'test', False)
        self.assertIsNone(ciphertexts)

    @patch('spacel.cli.secret.KmsCrypto')
    def test_encrypt(self, kms_crypto_factory):
        kms_crypto = MagicMock()
        kms_crypto_factory.return_value = kms_crypto

        ciphertexts = encrypt(self.app, 'test', False)
        self.assertEquals(1, len(ciphertexts))

        kms_crypto.encrypt.assert_called_once_with(ANY, 'test',
                                                   create_key=False)

    def test_update_manifest_no_key(self):
        helper = MagicMock()
        updated = update_manifest(helper, 'test', None, {})
        self.assertFalse(updated)

        helper.write_manifest.assert_not_called()

    def test_update_manifest_no_cipher_texts(self):
        helper = MagicMock()
        service_params = {}
        helper.read_manifest.return_value = {
            ORBIT_REGION: {
                'services': {
                    'test.service': service_params
                }
            }
        }
        updated = update_manifest(helper, 'test', TEST_KEY, {})
        self.assertFalse(updated)

    def test_update_manifest(self):
        helper = MagicMock()
        service_params = {}
        helper.read_manifest.return_value = {
            ORBIT_REGION: {
                'services': {
                    'test.service': service_params
                }
            }
        }
        updated = update_manifest(helper, 'test', TEST_KEY,
                                  {ORBIT_REGION: ENCRYPTED_PAYLOAD})
        self.assertTrue(updated)
        self.assertIn(TEST_KEY, service_params['environment'])
        helper.write_manifest.assert_called_with(ANY, 'app', ANY)
