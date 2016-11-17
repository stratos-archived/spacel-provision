import unittest

from spacel.model.orbit import Orbit
from test import ORBIT_NAME, ORBIT_REGION


class TestOrbit(unittest.TestCase):
    def setUp(self):
        self.orbit = Orbit(ORBIT_NAME, [ORBIT_REGION])

    def test_constructor_invalid_region(self):
        """Invalid region is ignored."""
        orbit = Orbit(ORBIT_NAME, [ORBIT_REGION, 'meow'])
        self.assertEquals({ORBIT_REGION}, set(orbit.regions.keys()))

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
        orbit = Orbit(ORBIT_NAME, [ORBIT_REGION])
        self.orbit_region = orbit.regions[ORBIT_REGION]
        self.orbit_region.deploy_stack = 'test-stack'
        self.orbit_region.parent_stack = 'test-stack'

    def test_valid_spacel(self):
        self.assertTrue(self.orbit_region.valid)

    def test_valid_spacel_invalid_instance_type(self):
        self.orbit_region.bastion_instance_type = 'meow'
        self.assertFalse(self.orbit_region.valid)

    def test_valid_spacel_invalid_nat(self):
        self.orbit_region.nat = 'meow'
        self.assertFalse(self.orbit_region.valid)

    def test_valid_gdh(self):
        self.orbit_region.provider = 'gdh'
        self.assertTrue(self.orbit_region.valid)

    def test_valid_gdh_ignore_spacel(self):
        self.orbit_region.provider = 'gdh'
        self.orbit_region.bastion_instance_type = 'meow'
        self.assertTrue(self.orbit_region.valid)

    def test_valid_gdh_no_deploy_stack(self):
        self.orbit_region.provider = 'gdh'
        self.orbit_region.deploy_stack = None
        self.assertFalse(self.orbit_region.valid)

    def test_valid_gdh_no_parent_stack(self):
        self.orbit_region.provider = 'gdh'
        self.orbit_region.parent_stack = None
        self.assertFalse(self.orbit_region.valid)
