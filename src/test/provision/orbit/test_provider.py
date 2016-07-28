from mock import MagicMock
import unittest

from spacel.model import Orbit
from spacel.model.orbit import (DEFAULTS, PROVIDER, REGIONS)
from spacel.provision.orbit.provider import ProviderOrbitFactory
from test.provision.orbit import (NAME, REGION)

TEST_PROVIDER = 'test'
REGION_LIST = [REGION]


class TestProviderOrbitFactory(unittest.TestCase):
    def setUp(self):
        self.provider = MagicMock()

        self.orbit_factory = ProviderOrbitFactory({
            TEST_PROVIDER: self.provider
        })

        self.orbit = Orbit({
            'name': NAME,
            REGIONS: REGION_LIST,
            DEFAULTS: {
                PROVIDER: TEST_PROVIDER
            }
        })

    def test_get_orbit(self):
        self.orbit_factory.get_orbit(self.orbit)
        self.provider.get_orbit.assert_called_once_with(self.orbit,
                                                        regions=REGION_LIST)

    def test_get_orbit_provider_not_found(self):
        self.orbit._params[DEFAULTS][PROVIDER] = 'does-not-exist'
        self.orbit_factory.get_orbit(self.orbit)
        self.provider.get_orbit.assert_not_called()

    def test_get(self):
        orbit_factory = ProviderOrbitFactory.get(None, None, None)
        self.assertEqual(2, len(orbit_factory._providers))
