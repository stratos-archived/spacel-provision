import unittest

from spacel.model import Orbit, SpaceApp

APP_NAME = 'test-app'

# Orbit parameters:
ORBIT_REGION = 'us-west-2'
ORBIT_NAME = 'test-orbit'
ORBIT_REGIONS = [ORBIT_REGION]
ORBIT_DOMAIN = 'test.com'

SECOND_REGION = 'us-east-1'
TWO_REGIONS = [ORBIT_REGION, SECOND_REGION]


class BaseSpaceAppTest(unittest.TestCase):
    def setUp(self):
        self.orbit = Orbit(ORBIT_NAME, ORBIT_REGIONS)
        self.assertTrue(self.orbit.valid)
        self.app = SpaceApp(self.orbit, APP_NAME)
        self.assertTrue(self.app.valid)
