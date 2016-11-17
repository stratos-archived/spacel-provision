from spacel.model.json.base import BaseJsonModelFactory, ALL

from test import BaseSpaceAppTest, ORBIT_REGION

ORBIT_NETWORK = '10.1'


class TestBaseJsonModelFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestBaseJsonModelFactory, self).setUp()
        self.factory = BaseJsonModelFactory()

    def test_set_property_all(self):
        self.factory._set_properties(self.orbit, {
            ALL: {'private_network': ORBIT_NETWORK}
        })
        self.assertNetwork()

    def test_set_property_region(self):
        self.factory._set_properties(self.orbit, {
            ALL: {'private_network': 'overwritten by region'},
            ORBIT_REGION: {'private_network': ORBIT_NETWORK}
        })
        self.assertNetwork()

    def test_set_property_bool_true(self):
        self.factory._set_properties(self.orbit, {
            ALL: {'private_nat_gateway': 'yes'}
        })
        self.assertTrue(self.orbit_region.private_nat_gateway)
        self.assertIsInstance(self.orbit_region.private_nat_gateway, bool)

    def test_set_property_bool_false(self):
        self.factory._set_properties(self.orbit, {
            ALL: {'private_nat_gateway': 'no'}
        })
        self.assertFalse(self.orbit_region.private_nat_gateway)
        self.assertIsInstance(self.orbit_region.private_nat_gateway, bool)

    def test_set_property_int(self):
        self.factory._set_properties(self.orbit, {
            ALL: {'bastion_instance_count': '2'}
        })
        self.assertEquals(2, self.orbit_region.bastion_instance_count)
        self.assertIsInstance(self.orbit_region.bastion_instance_count, int)

    def test_set_property_int_invalid(self):
        """Invalid ints are dropped (with a warning)."""
        self.factory._set_properties(self.orbit, {
            ALL: {'bastion_instance_count': 'fleventy-five'}
        })
        self.assertEquals(1, self.orbit_region.bastion_instance_count)

    def assertNetwork(self):
        self.assertEquals(ORBIT_NETWORK,
                          self.orbit.regions[ORBIT_REGION].private_network)
