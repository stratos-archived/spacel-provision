import unittest
from mock import MagicMock

from spacel.model import SpaceApp
from spacel.provision.cache.factory import CacheFactory

CACHE_NAME = 'test-cache'


class TestCacheFactory(unittest.TestCase):
    def setUp(self):
        self.resources = {}
        self.template = {'Resources': self.resources}
        self.cache_params = {}
        self.caches = {
            CACHE_NAME: self.cache_params
        }
        self.app = MagicMock(spec=SpaceApp)
        self.app.name = 'test-app'
        self.app.orbit = MagicMock()
        self.app.orbit.name = 'test-orbit'

        self.cache_factory = CacheFactory()

    def test_add_caches_noop(self):
        del self.caches[CACHE_NAME]
        self.cache_factory.add_caches(self.app, self.template, self.caches)
        self.assertEquals({}, self.resources)

    def test_add_caches_invalid_replicas(self):
        self.cache_params['replicas'] = 'meow'

        self.cache_factory.add_caches(self.app, self.template, self.caches)
        self.assertEquals({}, self.resources)

    def test_add_caches(self):
        self.cache_factory.add_caches(self.app, self.template, self.caches)
        self.assertEquals(2, len(self.resources))

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

    def test_instance_type_missing_ha(self):
        instance_type = self.cache_factory._instance_type({
            'instance_type': 'm3.large'
        }, True)
        self.assertEquals('cache.m3.large', instance_type)
