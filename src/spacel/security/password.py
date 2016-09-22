from botocore.exceptions import ClientError
import logging
from random import choice

from spacel.security.payload import EncryptedPayload

DICT = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%^*(-_=+)'

logger = logging.getLogger('spacel.security.password')


class PasswordManager(object):
    def __init__(self, clients, kms_crypt):
        self._clients = clients
        self._kms_crypt = kms_crypt

    def get_password(self, app, region, label, length=64, generate=True):
        """
        Get a password for an application in a region.
        :param app:  Application.
        :param region: Region.
        :param label: Password label.
        :param length: Password length.
        :return: Encrypted password.
        """
        name = app.name
        logger.debug('Getting password for %s in %s.', label, name)
        table_name = '%s-passwords' % app.orbit.name
        password_name = '%s:%s' % (name, label)

        dynamodb = self._clients.dynamodb(region)
        existing_item = dynamodb.get_item(TableName=table_name,
                                          Key={'name': {'S': password_name}}
                                          ).get('Item')
        if existing_item:
            logger.debug('Found existing password for %s in %s.', label, name)
            encrypted = EncryptedPayload.from_dynamodb_item(existing_item)

            def decrypt_func():
                return self._kms_crypt.decrypt_payload(encrypted)

            return encrypted, decrypt_func

        if not generate:
            return None, lambda: None

        # Not found, generate:
        logger.debug('Generating password for %s in %s.', label, name)
        plaintext = self._generate_password(length)
        encrypted_payload = self._kms_crypt.encrypt(app, region, plaintext)
        password_item = encrypted_payload.dynamodb_item()
        password_item['name'] = {'S': password_name}

        # Persist encrypted password:
        dynamodb.put_item(
            TableName=table_name,
            Item=password_item,
            ConditionExpression='attribute_not_exists(ciphertext)')

        # Plaintext can be returned _once_ without Decrypt() permission
        return encrypted_payload, lambda: plaintext

    def set_password(self, app, region, label, password_func):
        name = app.name
        logger.debug('Setting password for %s in %s.', label, name)
        table_name = '%s-passwords' % app.orbit.name
        password_name = '%s:%s' % (name, label)

        dynamodb = self._clients.dynamodb(region)
        existing_item = dynamodb.get_item(TableName=table_name,
                                          Key={'name': {'S': password_name}}
                                          ).get('Item')
        if existing_item:
            logger.warn('Existing password found for %s in %s, skipping.',
                        label, name)
            return False

        plaintext = password_func()
        encrypted_payload = self._kms_crypt.encrypt(app, region, plaintext)
        password_item = encrypted_payload.dynamodb_item()
        password_item['name'] = {'S': password_name}

        # Persist encrypted password:
        try:
            dynamodb.put_item(
                TableName=table_name,
                Item=password_item,
                ConditionExpression='attribute_not_exists(ciphertext)')
            return True
        except ClientError as e:
            logger.warn('Error saving encrypted password: %s', e)
            return False

    def decrypt(self, encrypted_payload):
        return self._kms_crypt.decrypt_payload(encrypted_payload)

    @staticmethod
    def _generate_password(length):
        return ''.join([choice(DICT) for _ in range(length)])
