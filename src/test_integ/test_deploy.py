import logging
import requests
import uuid

from spacel.provision.db.cache import REDIS_PORT, REDIS_VERSION
from test_integ import BaseIntegrationTest

logger = logging.getLogger('spacel.test.deploy')

APP_URL = 'https://%s' % BaseIntegrationTest.APP_HOSTNAME
UPGRADE_VERSION = '0.0.2'


class TestDeploy(BaseIntegrationTest):
    def test_01_deploy_simple_http(self):
        """Deploy a HTTP/S service, verify it's running."""
        self.provision()
        self._verify_deploy('http://%s' % BaseIntegrationTest.APP_HOSTNAME)
        self._verify_deploy()

    def test_02_upgrade(self):
        """Deploy a HTTPS service, upgrade and verify."""
        self.provision()

        self.app_params['services']['laika']['image'] = \
            self.image(UPGRADE_VERSION)
        self.provision()
        self._verify_deploy(version=UPGRADE_VERSION)

    def test_03_environment(self):
        """Deploy a service with custom environment variable, verify."""
        random_message = str(uuid.uuid4())
        self.app_params['services']['laika']['environment'] = {
            'MESSAGE': random_message
        }
        self.provision()
        self._verify_message(message=random_message)

    def test_04_cache(self):
        """Deploy a service with ElastiCache, verify."""
        self.app_params['caches'] = {
            'redis': {}
        }
        self.provision()
        self._verify_redis()

    def _verify_deploy(self, url=APP_URL, version=None):
        version = version or BaseIntegrationTest.APP_VERSION
        r = requests.get(url)
        self.assertEquals(version, r.json()['version'])

    def _verify_message(self, url=APP_URL, message=''):
        r = requests.get('%s/environment' % url)
        self.assertEquals(message, r.json()['message'])

    def _verify_redis(self, url=APP_URL):
        r = requests.get('%s/redis/info' % url)
        redis_info = r.json()
        self.assertEquals(REDIS_PORT, redis_info['tcp_port'])
        self.assertEquals(REDIS_VERSION, redis_info['redis_version'])