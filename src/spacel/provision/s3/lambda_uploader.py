from io import BytesIO
import os
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from spacel.provision.s3.base import BaseUploader


class LambdaUploader(BaseUploader):
    def __init__(self, clients, region, bucket):
        super(LambdaUploader, self).__init__(clients, region, bucket)
        self._cache = {}
        file_path = os.path.dirname(os.path.realpath(__file__))
        self._path = os.path.join(file_path, '..', '..', 'lambda')

    def _load(self, template):
        cached = self._cache.get(template)
        if cached:
            return cached

        template_path = os.path.join(self._path, template)
        with open(template_path) as template_in:
            loaded = template_in.read()
            self._cache[template] = loaded
            return loaded

    def upload(self, name, expansions=None):
        # Load and customize script:
        script = self._load(name)
        if expansions:
            for key, value in expansions.items():
                script = script.replace(key, value)
        encoded_script = script.encode('utf-8')

        # Hash script
        script_hash = self._hash(encoded_script)

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
        self._upload(zip_path, zip_buffer)
        return self._bucket, zip_path
