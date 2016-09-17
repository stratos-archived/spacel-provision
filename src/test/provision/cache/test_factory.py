import json
from mock import MagicMock
import unittest

from spacel.model import SpaceApp
from spacel.provision.cache.factory import CacheFactory
from spacel.provision.template import IngressResourceFactory

CACHE_NAME = 'test-cache'
REGION = 'us-west-2'


class TestCacheFactory(unittest.TestCase):
    def setUp(self):
        self.user_data_params = [
            '{',
            '\"caches\":{',
            '} }'
        ]
        self.resources = {
            'Lc': {
                'Properties': {
                    'UserData': {
                        'Fn::Base64': {
                            'Fn::Join': [
                                '', self.user_data_params
                            ]
                        }
                    }
                }
            }
        }
        self.template = {'Resources': self.resources}
        self.cache_params = {}
        self.caches = {
            CACHE_NAME: self.cache_params
        }
        self.app = MagicMock(spec=SpaceApp)
        self.app.name = 'test-app'
        self.app.orbit = MagicMock()
        self.app.orbit.name = 'test-orbit'

        self.ingress = MagicMock(spec=IngressResourceFactory)
        self.cache_factory = CacheFactory(self.ingress)

    def test_add_caches_noop(self):
        del self.caches[CACHE_NAME]
        self.cache_factory.add_caches(self.app, REGION, self.template, self.caches)
        self.assertEquals(1, len(self.resources))

    def test_add_caches_invalid_replicas(self):
        self.cache_params['replicas'] = 'meow'

        self.cache_factory.add_caches(self.app, REGION, self.template, self.caches)
        self.assertEquals(1, len(self.resources))

    def test_add_caches(self):
        self.cache_factory.add_caches(self.app, REGION, self.template, self.caches)
        self.assertEquals(3, len(self.resources))

        # Resolve {'Ref':}s to a string:
        for index, user_data in enumerate(self.user_data_params):
            if isinstance(user_data, dict):
                self.user_data_params[index] = user_data['Ref']

        # UserData should be valid JSON, `caches` should reference
        user_data = json.loads(''.join(self.user_data_params))
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

    def test_instance_type_missing_ha(self):
        instance_type = self.cache_factory._instance_type({
            'instance_type': 'm3.large'
        }, True)
        self.assertEquals('cache.m3.large', instance_type)
