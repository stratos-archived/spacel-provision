import unittest

from spacel.model.orbit import Orbit, OrbitRegion
from test import ORBIT_NAME, ORBIT_REGION


class TestOrbit(unittest.TestCase):
    def setUp(self):
        self.orbit = Orbit(ORBIT_NAME, [ORBIT_REGION])

    def test_constructor_invalid_region(self):
        orbit = Orbit(ORBIT_NAME, [ORBIT_REGION, 'meow'])
        self.assertEquals({ORBIT_REGION}, orbit.regions.keys())

    def test_valid(self):
        self.assertTrue(self.orbit.valid)

    def test_valid_no_name(self):
        self.orbit.name = None
        self.assertFalse(self.orbit.valid)

    def test_valid_no_regions(self):
        self.orbit.regions = []
        self.assertFalse(self.orbit.valid)

    def test_valid_invalid_region(self):
        self.orbit.regions[ORBIT_REGION].provider = None
        self.assertFalse(self.orbit.valid)


class TestOrbitRegion(unittest.TestCase):
    def setUp(self):
        self.orbit_region = OrbitRegion()

    def test_valid_spacel(self):
        self.orbit_region.provider = 'spacel'
        self.assertTrue(self.orbit_region.valid)

    def test_valid_gdh(self):
        self.orbit_region.provider = 'gdh'
        self.assertTrue(self.orbit_region.valid)
