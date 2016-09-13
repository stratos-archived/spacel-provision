import json
from spacel.provision.s3.base import BaseUploader


class TemplateUploader(BaseUploader):
    def upload(self, template, app_name):
        template_body = json.dumps(template, indent=2)

        template_hash = self._hash(template_body)
        path = '%s/%s.template' % (app_name, template_hash)
        self._upload(path, template_body)
