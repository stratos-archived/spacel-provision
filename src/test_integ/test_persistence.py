from spacel.provision.app.db.cache import REDIS_PORT, REDIS_VERSION
from spacel.provision.app.db.rds import POSTGRES_PORT, POSTGRES_VERSION
from test_integ import BaseIntegrationTest


class TestDeployPersistence(BaseIntegrationTest):
    def test_01_disk(self):
        """Deploy a service with persistent EBS volume, verify."""
        for app_region in self.app.regions.values():
            # 1 EBS volume, which can only by used by 1 instance at a time:
            app_region.instance_max = 1
            app_region.volumes['data0'] = {
                'count': 1,
                'size': 1
            }

            # Mounted by docker service:, configured by application:
            laika_service = app_region.services['laika']
            laika_service.volumes['/mnt/data0'] = '/mnt/data'
            laika_service.environment['DISK_PATH'] = '/mnt/data/file.txt'

        self.provision()

        initial = self._verify_counter('disk')
        self.assertNotEquals(0, initial)

        # Upgrade, verify persistence:
        self.image(BaseIntegrationTest.UPGRADE_VERSION)
        self.provision()
        self._verify_counter('disk', expected_count=initial)

    def test_02_cache(self):
        """Deploy a service with ElastiCache, verify."""
        for app_region in self.app.regions.values():
            app_region.caches['redis'] = {}
        self.provision()

        # Info path:
        r = self._get('redis/info')
        redis_info = r.json()
        self.assertEquals(REDIS_PORT, redis_info['tcp_port'])
        self.assertEquals(REDIS_VERSION, redis_info['redis_version'])

        self._verify_counter('redis', post_count=10)

    def test_03_rds(self):
        """Deploy a service with RDS, verify."""
        for app_region in self.app.regions.values():
            app_region.databases['postgres'] = {}
        self.provision()

        # Info path:
        r = self._get('postgres/info')
        postgres_info = r.json()
        self.assertEquals(str(POSTGRES_PORT), postgres_info['port'])
        self.assertEquals(POSTGRES_VERSION, postgres_info['server_version'])

        self._verify_counter('postgres', post_count=10)

    def _verify_counter(self, counter_type, expected_count=0, post_count=10):
        counter_url = '%s/counter' % counter_type
        r = self._get(counter_url)
        count = r.json()['count']
        self.assertTrue(count >= expected_count)
        for i in range(post_count):
            r = self._post(counter_url)
            count = r.json()['count']
        return count
