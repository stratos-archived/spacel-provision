from mock import MagicMock

from spacel.provision.orbit.provider import ProviderOrbitFactory
from test import BaseSpaceAppTest, ORBIT_REGION

TEST_PROVIDER = 'test'


class TestProviderOrbitFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestProviderOrbitFactory, self).setUp()

        self.provider = MagicMock()
        self.orbit_factory = ProviderOrbitFactory({
            TEST_PROVIDER: self.provider
        })
        self.orbit.regions[ORBIT_REGION].provider = TEST_PROVIDER

    def test_get_orbit(self):
        self.orbit_factory.orbit(self.orbit)
        self.provider.orbit.assert_called_once_with(self.orbit,
                                                    regions=[ORBIT_REGION])

    def test_get_orbit_provider_not_found(self):
        self.orbit.regions[ORBIT_REGION].provider = 'does-not-exist'
        self.orbit_factory.orbit(self.orbit)
        self.provider.orbit.assert_not_called()

    def test_get(self):
        orbit_factory = ProviderOrbitFactory.get(None, None, None, None, None,
                                                 None)
        self.assertEqual(2, len(orbit_factory._providers))
