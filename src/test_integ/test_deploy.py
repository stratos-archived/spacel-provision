import logging
import requests

from test_integ import BaseIntegrationTest

logger = logging.getLogger('spacel.test.deploy')

APP_URL = 'https://%s' % BaseIntegrationTest.APP_HOSTNAME
UPGRADE_VERSION = '0.0.2'


class TestDeploy(BaseIntegrationTest):
    def test_01_deploy_simple_http(self):
        """Deploy a HTTP/S service, verify it's running."""
        self.provision()
        self._verify_deploy('http://%s' % BaseIntegrationTest.APP_HOSTNAME)
        self._verify_deploy(APP_URL)

    def test_02_upgrade(self):
        """Deploy a HTTPS service, upgrade and verify."""
        self.provision()

        self.app_params['services']['laika']['image'] = \
            self.image(UPGRADE_VERSION)
        self.provision()
        self._verify_deploy(APP_URL, version=UPGRADE_VERSION)

    def _verify_deploy(self, url, version=BaseIntegrationTest.APP_VERSION):
        r = requests.get(url)
        self.assertEquals(version, r.json()['version'])
