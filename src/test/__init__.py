import unittest

from spacel.model import Orbit, SpaceApp
from spacel.model.orbit import (NAME, DOMAIN, REGIONS)

ORBIT_NAME = 'test-orbit'
APP_NAME = 'test-app'
REGION = 'us-west-2'


class BaseSpaceAppTest(unittest.TestCase):
    def setUp(self):
        self.orbit = Orbit({
            NAME: ORBIT_NAME,
            DOMAIN: 'test.com',
            REGIONS: [REGION]
        })

        self.app = SpaceApp(self.orbit, {
            'name': APP_NAME
        })
