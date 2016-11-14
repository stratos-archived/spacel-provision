import json
import uuid

from test_integ import BaseIntegrationTest

ENCRYPTED_ENV = {
    'ciphertext': '5nBQVtS4VxIZmtW/x74Dfaz2cdjySWbSYhlkIPZUVjs=',
    'encoding': 'utf-8',
    'iv': 'xmPEWRKiaVCY7SN5P0/QxA==',
    'key': 'AQEDAHi4BV5h2C+ZP+MPN8eO2fjkxzg4fd3wni5WSzyTEp2YrgAAAH4wfAYJKoZIhvc'
           'NAQcGoG8wbQIBADBoBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDA1VD1y9FUO6q5'
           '1ikQIBEIA7kmMpEXBdWzWgknNLa9mlw/If+MXn/FI9eLHNP4BxqzqVr6rVGAsiNQtmS'
           'hsGZDxQGT7WJbFV8VnhVaM=',
    'key_region': 'us-east-1'
}


class TestDeploy(BaseIntegrationTest):
    def test_01_deploy_simple_http(self):
        """Deploy a HTTP/S service, verify it's running."""
        self.provision()
        self._verify_deploy()

    def test_02_upgrade(self):
        """Deploy a HTTPS service, upgrade and verify."""
        self.provision()

        self.image(BaseIntegrationTest.UPGRADE_VERSION)
        self.provision()
        self._verify_deploy(version=BaseIntegrationTest.UPGRADE_VERSION)

    def test_03_environment(self):
        """Deploy a service with custom environment variable, verify."""
        random_message = str(uuid.uuid4())
        self.app_params['services']['laika']['environment'] = {
            'MESSAGE': random_message
        }
        self.provision()
        self._verify_message(message=random_message)

    def test_04_systemd(self):
        """Deploy a service with fulltext systemd unit."""
        self._set_unit_file('''[Unit]
Description=Fulltext unit
Requires=spacel-agent.service

[Service]
User=space
TimeoutStartSec=0
Restart=always
StartLimitInterval=0
ExecStartPre=-/usr/bin/docker pull {0}
ExecStartPre=-/usr/bin/docker kill %n
ExecStartPre=-/usr/bin/docker rm %n
ExecStart=/usr/bin/docker run --rm --name %n -p 80:8080 -e MESSAGE=handwritten {0}
ExecStop=/usr/bin/docker stop %n
'''.format('pebbletech/spacel-laika:latest'))

        self.provision()
        self._verify_message('handwritten')

    def test_05_encrypted_file(self):
        """Encrypted file is decrypted."""
        self.app_params['files'] = {'laika.env': ENCRYPTED_ENV}
        self.provision()
        self._verify_message('top secret')

    def test_06_encrypted_entry(self):
        """Encrypted file is decrypted."""
        self.app_params['files'] = {
            'laika.env': 'MESSAGE=%s' % json.dumps(ENCRYPTED_ENV)
        }
        self.provision()
        self._verify_message('top secret')

    def _verify_deploy(self, version=None):
        version = version or BaseIntegrationTest.APP_VERSION
        r = self._get('')
        self.assertEquals(version, r.json()['version'])

    def _verify_message(self, message=''):
        r = self._get('environment')
        self.assertEquals(message, r.json()['message'])
