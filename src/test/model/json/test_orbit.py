import json
import unittest

from spacel.model.json.base import NAME, REGIONS, ALL
from spacel.model.json.orbit import OrbitJsonModelFactory
from test import ORBIT_NAME, ORBIT_REGION, ORBIT_DOMAIN

ORBIT_NETWORK = '10.1'


class TestOrbitJsonModelFactory(unittest.TestCase):
    def setUp(self):
        self.orbit_factory = OrbitJsonModelFactory()
        self.params = {
            NAME: ORBIT_NAME,
            REGIONS: [ORBIT_REGION],
            ALL: {
                'domain': ORBIT_DOMAIN,  # Only set in defaults
                'private_network': '10.0'  # Overwritten by region
            },
            ORBIT_REGION: {
                'private_network': ORBIT_NETWORK
            }
        }

    def test_orbit_no_regions(self):
        del self.params[REGIONS]
        orbit = self.orbit_factory.orbit(self.params)
        self.assertFalse(orbit.valid)

    def test_orbit_region_from_all(self):
        orbit = self.orbit_factory.orbit(self.params)
        self.assertEquals(ORBIT_DOMAIN, orbit.regions[ORBIT_REGION].domain)

    def test_orbit_region_from_region(self):
        orbit = self.orbit_factory.orbit(self.params)
        self.assertEquals(ORBIT_NETWORK,
                          orbit.regions[ORBIT_REGION].private_network)

    def test_orbit_valid(self):
        orbit = self.orbit_factory.orbit(self.params)
        self.assertTrue(orbit.valid)

    def test_sample_develop(self):
        orbit = self._load_sample('develop.json')
        self.assertEquals('develop', orbit.name)
        self.assertEquals(2, len(orbit.regions))
        self.assertTrue(orbit.valid)

        orbit_east1 = orbit.regions['us-east-1']
        self.assertEquals(0, orbit_east1.bastion_instance_count)
        self.assertEquals('pebbledev.com', orbit_east1.domain)
        self.assertEquals('spacel', orbit_east1.provider)

        orbit_west2 = orbit.regions['us-west-2']
        self.assertEquals(1, orbit_west2.bastion_instance_count)
        self.assertEquals('pebbledev.com', orbit_west2.domain)
        self.assertEquals('gdh', orbit_west2.provider)
        self.assertEquals('git-deploy', orbit_west2.parent_stack)
        self.assertEquals('git-deploy-develop', orbit_west2.deploy_stack)

    def test_sample_sl_test(self):
        orbit = self._load_sample('sl-test.json')
        self.assertEquals('sl-test', orbit.name)
        self.assertEquals(1, len(orbit.regions))
        self.assertTrue(orbit.valid)

    def _load_sample(self, sample_name):
        with open('../sample/orbit/%s' % sample_name) as sample_in:
            sample_json = json.load(sample_in)
            return self.orbit_factory.orbit(sample_json)
