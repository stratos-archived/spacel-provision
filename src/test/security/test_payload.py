import unittest

from spacel.security.payload import EncryptedPayload
from test import ORBIT_REGION

IV = b'0000000000000000'
CIPHERTEXT = b'0000000000000000'
KEY = b'0000000000000000'
ENCODING = 'utf-8'
ENCRYPTED_PAYLOAD = EncryptedPayload(IV, CIPHERTEXT, KEY, ORBIT_REGION,
                                     ENCODING)


class TestEncryptedPayload(unittest.TestCase):
    def setUp(self):
        self.payload = ENCRYPTED_PAYLOAD

    def test_round_trip_dynamodb(self):
        dynamodb_item = self.payload.dynamodb_item()
        payload = EncryptedPayload.from_dynamodb_item(dynamodb_item)
        self.assertEquals(IV, payload.iv)
        self.assertEquals(CIPHERTEXT, payload.ciphertext)
        self.assertEquals(KEY, payload.key)
        self.assertEquals(ORBIT_REGION, payload.key_region)
        self.assertEquals(ENCODING, payload.encoding)

    def test_round_trip_json(self):
        as_json = self.payload.json()
        payload = EncryptedPayload.from_json(as_json)
        self.assertEquals(IV, payload.iv)
        self.assertEquals(CIPHERTEXT, payload.ciphertext)
        self.assertEquals(KEY, payload.key)
        self.assertEquals(ORBIT_REGION, payload.key_region)
        self.assertEquals(ENCODING, payload.encoding)

    def test_from_json_not_json(self):
        payload = EncryptedPayload.from_json('meow')
        self.assertIsNone(payload)

    def test_from_json_invalid_json(self):
        payload = EncryptedPayload.from_json('{}')
        self.assertIsNone(payload)
