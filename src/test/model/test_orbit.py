import unittest

from spacel.model import NAME, REGIONS, DEFAULTS
from spacel.model.orbit import (Orbit,
                                BASTION_INSTANCE_COUNT,
                                BASTION_INSTANCE_TYPE,
                                PRIVATE_NETWORK)
from test import ORBIT_NAME, ORBIT_REGION, TWO_REGIONS

NETWORK = '192.168.0.0/16'


class TestOrbit(unittest.TestCase):
    def setUp(self):
        self.params = {
            NAME: ORBIT_NAME,
            REGIONS: TWO_REGIONS,
            DEFAULTS: {
                PRIVATE_NETWORK: NETWORK,
            },
            ORBIT_REGION: {
                BASTION_INSTANCE_TYPE: 't2.small',
                BASTION_INSTANCE_COUNT: 2
            }
        }
        self.orbit = Orbit(self.params)
