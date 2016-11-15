import unittest

from spacel.model import Orbit
from spacel.model.json.app import SpaceAppJsonModelFactory
from spacel.model.json.base import NAME, REGIONS, ALL
from test import ORBIT_NAME, ORBIT_REGION, APP_NAME


class TestSpaceAppJsonModelFactory(unittest.TestCase):
    def setUp(self):
        self.factory = SpaceAppJsonModelFactory()
        self.orbit = Orbit(ORBIT_NAME, [ORBIT_REGION])
        self.params = {
            NAME: APP_NAME,
            REGIONS: [ORBIT_REGION],
            ALL: {
                'instance_type': 't2.micro'
            }
        }

    def test_app_no_regions(self):
        """When app doesn't specify regions, all orbit regions."""
        del self.params[REGIONS]
        app = self._app()
        self.assertEquals({ORBIT_REGION}, app.regions.keys())
        self.assertTrue(app.valid)

    def test_app_region_not_in_orbit(self):
        """Valid region that isn't part of orbit is dropped."""
        self.params[REGIONS] += ['eu-west-1']
        app = self._app()
        self.assertEquals({ORBIT_REGION}, app.regions.keys())
        self.assertTrue(app.valid)

    def _app(self):
        return self.factory.app(self.orbit, self.params)
