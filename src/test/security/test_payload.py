import json
import unittest

from spacel.security.payload import EncryptedPayload
from test import ORBIT_REGION

IV = b'0000000000000000'
CIPHERTEXT = b'0000000000000000'
KEY = b'0000000000000000'
ENCODING = 'utf-8'


class TestEncryptedPayload(unittest.TestCase):
    def setUp(self):
        self.payload = EncryptedPayload(IV, CIPHERTEXT, KEY, ORBIT_REGION, ENCODING)

    def test_roundtrip_dynamodb(self):
        dynamodb_item = self.payload.dynamodb_item()
        payload = EncryptedPayload.from_dynamodb_item(dynamodb_item)
        self.assertEquals(IV, payload.iv)
        self.assertEquals(CIPHERTEXT, payload.ciphertext)
        self.assertEquals(KEY, payload.key)
        self.assertEquals(ORBIT_REGION, payload.key_region)
        self.assertEquals(ENCODING, payload.encoding)

    def test_roundtrip_json(self):
        as_json = self.payload.json()
        payload = EncryptedPayload.from_json(as_json)
        self.assertEquals(IV, payload.iv)
        self.assertEquals(CIPHERTEXT, payload.ciphertext)
        self.assertEquals(KEY, payload.key)
        self.assertEquals(ORBIT_REGION, payload.key_region)
        self.assertEquals(ENCODING, payload.encoding)
