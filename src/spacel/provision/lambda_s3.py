import codecs
import hashlib
from io import BytesIO
import os
import six
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


class LambdaUploader(object):
    def __init__(self, clients, region, bucket):
        self._s3 = clients.s3(region)
        self._bucket = bucket
        self._cache = {}

    def _load(self, template):
        cached = self._cache.get(template)
        if cached:
            return cached

        template_path = os.path.join('lambda', template)
        with open(template_path) as template_in:
            loaded = template_in.read()
            self._cache[template] = loaded
            return loaded

    def upload(self, name, expansions={}):
        # Load and customize script:
        script = self._load(name)
        for key, value in expansions.items():
            script = script.replace(key, value)
        encoded_script = script.encode('utf-8')

        # Hash script+endpoint (which is common across the environment)
        script_hasher = hashlib.sha1()
        script_hasher.update(encoded_script)
        script_hash = codecs.encode(script_hasher.digest(), 'hex')
        if six.PY2:
            script_hash = str(script_hash)
        else:
            script_hash = str(script_hash, 'utf-8')

        # Package into zipfile:
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            zip_info = ZipInfo('index.js')
            zip_info.compress_type = ZIP_DEFLATED
            zip_info.external_attr = 0o0755 << 16
            zip_file.writestr(zip_info, encoded_script)
        zip_buffer.seek(0)

        # Upload to S3:
        zip_path = '%s/%s.zip' % (name, script_hash)

        s3_object = self._s3.Object(self._bucket, zip_path)
        s3_object.put(Body=zip_buffer)
        return self._bucket, zip_path
