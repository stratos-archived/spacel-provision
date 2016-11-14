import unittest

from spacel.model.base import BaseModelObject, DEFAULTS, NAME, REGIONS
from test import ORBIT_REGION, SECOND_REGION, TWO_REGIONS

TEST_KEY = 'test'
TEST_VALUE = 'test-value'
DEFAULT_VALUE = 'default'


class TestBaseModelObject(unittest.TestCase):
    def setUp(self):
        self.bmo = BaseModelObject({
            NAME: TEST_VALUE,
            REGIONS: TWO_REGIONS,
            DEFAULTS: {
                TEST_KEY: DEFAULT_VALUE
            },
            ORBIT_REGION: {
                TEST_KEY: ORBIT_REGION
            }
        })

    def test_no_params(self):
        self.bmo = BaseModelObject()
        self.assertIsNone(self.bmo.name)
        self.assertEquals([], self.bmo.regions)
        self.assertFalse(self.bmo.valid)

    def test_params(self):
        self.assertEquals(TEST_VALUE, self.bmo.name)
        self.assertEquals(TWO_REGIONS, self.bmo.regions)
        self.assertTrue(self.bmo.valid)

    def test_regions_invalid(self):
        self.bmo = BaseModelObject({
            NAME: TEST_VALUE,
            REGIONS: ['meow'] + TWO_REGIONS
        })
        self.assertEquals(TWO_REGIONS, self.bmo.regions)
        self.assertFalse(self.bmo.valid)

    def test_get_param_defaults(self):
        value = self.bmo._get_param(SECOND_REGION, TEST_KEY)
        self.assertEquals(DEFAULT_VALUE, value)

    def test_get_param_class_defaults(self):
        other_value = self.bmo._get_param(SECOND_REGION, 'other-key')
        self.assertIsNone(other_value)

    def test_get_param_region(self):
        instance = self.bmo._get_param(ORBIT_REGION, TEST_KEY)
        self.assertEquals(ORBIT_REGION, instance)
