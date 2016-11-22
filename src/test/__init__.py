import unittest

from botocore.exceptions import ClientError

from spacel.model import Orbit, OrbitRegion, SpaceApp, SpaceAppRegion, \
    SpaceServicePort

APP_NAME = 'test-app'

# Orbit parameters:
ORBIT_REGION = 'us-west-2'
ORBIT_NAME = 'test-orbit'
ORBIT_REGION_AZS = ['us-west-2a', 'us-west-2b', 'us-west-2c']
ORBIT_DOMAIN = 'test.com'

OTHER_REGION = 'us-east-1'
OTHER_REGION_AZS = ['us-east-1a', 'us-east-1b', 'us-east-1c']


class BaseSpaceAppTest(unittest.TestCase):
    def setUp(self):
        self.orbit = Orbit(ORBIT_NAME, [ORBIT_REGION], domain=ORBIT_DOMAIN)
        self.assertTrue(self.orbit.valid)
        self.orbit_region = self.orbit.regions[ORBIT_REGION]
        self.orbit_region.az_keys = ORBIT_REGION_AZS

        self.app = SpaceApp(self.orbit, APP_NAME)
        self.assertTrue(self.app.valid)
        self.app_region = self.app.regions[ORBIT_REGION]
        self.app_region.public_ports[80] = SpaceServicePort(80)

        # Unused regions:
        self.other_orbit_region = OrbitRegion(self.orbit, OTHER_REGION)
        self.other_orbit_region.az_keys = OTHER_REGION_AZS
        self.other_app_region = SpaceAppRegion(self.app,
                                               self.other_orbit_region)

    def _multi_region(self):
        self.orbit.regions[OTHER_REGION] = self.other_orbit_region
        self.app.regions[OTHER_REGION] = self.other_app_region

    @staticmethod
    def _client_error(message='Kaboom', operation='DescribeKey'):
        return ClientError({'Error': {'Message': message}}, operation)
