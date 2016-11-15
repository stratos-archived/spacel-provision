import unittest

from spacel.model import Orbit
from spacel.model.json.base import BaseJsonModelFactory, ALL
from test import ORBIT_NAME, ORBIT_REGION

ORBIT_NETWORK = '10.1'


class TestBaseJsonModelFactory(unittest.TestCase):
    def setUp(self):
        self.factory = BaseJsonModelFactory()
        self.obj = Orbit(ORBIT_NAME, [ORBIT_REGION])

    def test_set_property_all(self):
        self.factory._set_properties(self.obj, {
            ALL: {'private_network': ORBIT_NETWORK}
        })
        self.assertNetwork()

    def test_set_property_region(self):
        self.factory._set_properties(self.obj, {
            ALL: {'private_network': 'overwritten by region'},
            ORBIT_REGION: {'private_network': ORBIT_NETWORK}
        })
        self.assertNetwork()

    def assertNetwork(self):
        self.assertEquals(ORBIT_NETWORK,
                          self.obj.regions[ORBIT_REGION].private_network)
