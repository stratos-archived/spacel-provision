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

    def test_04_disk(self):
        # 1 EBS volume, which can only by used by 1 instance at a time:
        self.app_params['instance_max'] = 1
        self.app_params['volumes'] = {
            'data0': {
                'count': 1,
                'size': 1
            }
        }
        # Mounted by docker service:
        self.app_params['services']['laika']['volumes'] = {
            '/mnt/data0': '/mnt/data'
        }
        # Configured by application:
        self.app_params['services']['laika']['environment'] = {
            'DISK_PATH': '/mnt/data/file.txt'
        }

        self.provision()

        initial = self._verify_disk()
        self.assertNotEquals(0, initial)

        # Upgrade, verify persistence:
        self.image(UPGRADE_VERSION)
        self.provision()
        self._verify_disk(expected_count=initial)

    def test_05_cache(self):
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

    def _verify_disk(self, url=APP_URL, expected_count=0, post_count=10):
        counter_url = '%s/disk/counter' % url
        r = requests.get(counter_url)
        count = r.json()['count']
        self.assertTrue(count >= expected_count)

        for i in range(post_count):
            r = requests.post(counter_url)
            count = r.json()['count']
        return count
