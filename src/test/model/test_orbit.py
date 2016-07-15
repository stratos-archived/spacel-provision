import unittest

from spacel.model.orbit import (Orbit, PRIVATE_NETWORK, BASTION_INSTANCE_TYPE,
                                BASTION_INSTANCE_COUNT)

NAME = 'test'
REGION = 'us-east-1'
REGION2 = 'us-west-2'
NETWORK = '192.168.0.0/16'


class TestOrbit(unittest.TestCase):
    def setUp(self):
        self.params = {
            'regions': (REGION, REGION2),
            'defaults': {
                PRIVATE_NETWORK: NETWORK,
            },
            REGION: {
                BASTION_INSTANCE_TYPE: 't2.small',
                BASTION_INSTANCE_COUNT: 2
            }
        }
        self.orbit = Orbit(NAME, self.params)

    def test_get_value_param_defaults(self):
        network = self.orbit.get_param(REGION2, PRIVATE_NETWORK)
        self.assertEquals(NETWORK, network)

    def test_get_value_class_defaults(self):
        network = self.orbit.get_param(REGION2, BASTION_INSTANCE_TYPE)
        self.assertEquals('t2.nano', network)

    def test_get_value_region(self):
        instance = self.orbit.get_param(REGION, BASTION_INSTANCE_COUNT)
        self.assertEquals(2, instance)
