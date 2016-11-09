import logging
import uuid

from test_integ import BaseIntegrationTest

logger = logging.getLogger('spacel.test.deploy')


class TestDeploy(BaseIntegrationTest):
    def test_01_deploy_simple_http(self):
        """Deploy a HTTP/S service, verify it's running."""
        self.provision()
        self._verify_deploy('http://%s' % BaseIntegrationTest.APP_HOSTNAME)
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
        del self.app_params['services']['laika']['image']
        self.app_params['services']['laika']['unit_file'] = '''[Unit]
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
'''.format('pebbletech/spacel-laika:latest')

        self.provision()
        self._verify_message('handwritten')

    def _verify_deploy(self, version=None):
        version = version or BaseIntegrationTest.APP_VERSION
        r = self._get('')
        self.assertEquals(version, r.json()['version'])

    def _verify_message(self, message=''):
        r = self._get('environment')
        self.assertEquals(message, r.json()['message'])
