import unittest

from spacel.model import Orbit, SpaceApp

ORBIT_NAME = 'test-orbit'
APP_NAME = 'test-app'
REGION = 'us-west-2'


class BaseSpaceAppTest(unittest.TestCase):
    def setUp(self):
        self.orbit = Orbit({
            'name': ORBIT_NAME,
            'domain': 'test.com'
        })

        self.app = SpaceApp(self.orbit, {
            'name': APP_NAME
        })
