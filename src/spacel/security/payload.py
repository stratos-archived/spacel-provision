import json
from spacel.provision import base64_encode


class EncryptedPayload(object):
    def __init__(self, iv, ciphertext, key, key_region, encoding):
        self.iv = iv
        self.ciphertext = ciphertext
        self.key = key
        self.key_region = key_region
        self.encoding = encoding

    def dynamodb_item(self):
        return {
            'iv': {'B': self.iv},
            'key': {'B': self.key},
            'key_region': {'S': self.key_region},
            'ciphertext': {'B': self.ciphertext},
            'encoding': {'S': self.encoding}
        }

    @staticmethod
    def from_dynamodb_item(item):
        return EncryptedPayload(
            item['iv']['B'],
            item['ciphertext']['B'],
            item['key']['B'],
            item['key_region']['S'],
            item['encoding']['S'])

    def json(self):
        return json.dumps({
            'iv': base64_encode(self.iv),
            'key': base64_encode(self.key),
            'key_region': self.key_region,
            'ciphertext': base64_encode(self.ciphertext),
            'encoding': self.encoding,
        })
