import codecs
import hashlib
import six


class BaseUploader(object):
    def __init__(self, clients, region, bucket):
        self._s3 = clients.s3(region)
        self._bucket = bucket

    @staticmethod
    def _hash(data):
        script_hasher = hashlib.sha1()
        if isinstance(data, six.string_types):
            data = data.encode('utf-8')
        script_hasher.update(data)
        script_hash = codecs.encode(script_hasher.digest(), 'hex')
        if six.PY2:
            return str(script_hash)
        else:
            return str(script_hash, 'utf-8')

    def _upload(self, path, body):
        s3_object = self._s3.Object(self._bucket, path)
        s3_object.put(Body=body)
