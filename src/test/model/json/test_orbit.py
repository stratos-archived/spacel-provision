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
