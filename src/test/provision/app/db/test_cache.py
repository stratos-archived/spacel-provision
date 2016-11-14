from spacel.provision.app.db.cache import CacheFactory
from test import ORBIT_REGION
from test.provision.app.db import BaseDbTest

CACHE_NAME = 'test-cache'


class TestCacheFactory(BaseDbTest):
    def setUp(self):
        super(TestCacheFactory, self).setUp()
        self.user_data_params += [
            '{',
            '\"caches\":{',
            '} }'
        ]
        self.cache_params = {}
        self.caches = {
            CACHE_NAME: self.cache_params
        }

        self.cache_factory = CacheFactory(self.ingress)

    def test_add_caches_noop(self):
        del self.caches[CACHE_NAME]
        self.cache_factory.add_caches(self.app, ORBIT_REGION, self.template,
                                      self.caches)
        self.assertEquals(1, len(self.resources))

    def test_add_caches_invalid_replicas(self):
        self.cache_params['replicas'] = 'meow'

        self.cache_factory.add_caches(self.app, ORBIT_REGION, self.template,
                                      self.caches)
        self.assertEquals(1, len(self.resources))

    def test_add_caches(self):
        self.cache_factory.add_caches(self.app, ORBIT_REGION, self.template,
                                      self.caches)
        self.assertEquals(4, len(self.resources))

        # UserData should be valid JSON, `caches` should reference
        user_data = self._user_data()
        self.assertEquals('Cachetestcache', user_data['caches'][CACHE_NAME])

    def test_replicas_invalid(self):
        replicas = self.cache_factory._replicas({'replicas': 'meow'})
        self.assertIsNone(replicas)

    def test_replicas_missing(self):
        replicas = self.cache_factory._replicas({})
        self.assertEquals(0, replicas)

    def test_replicas(self):
        replicas = self.cache_factory._replicas({'replicas': '1'})
        self.assertEquals(1, replicas)

    def test_instance_type_missing(self):
        instance_type = self.cache_factory._instance_type({}, False)
        self.assertEquals('cache.t2.micro', instance_type)

    def test_instance_type_missing_ha(self):
        instance_type = self.cache_factory._instance_type({}, True)
        self.assertEquals('cache.m3.medium', instance_type)

    def test_instance_type_add_prefix(self):
        instance_type = self.cache_factory._instance_type({
            'instance_type': 't2.micro'
        }, True)
        self.assertEquals('cache.t2.micro', instance_type)
