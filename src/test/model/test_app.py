from spacel.model.app import SpaceApp, SpaceServicePort
from test import BaseSpaceAppTest, APP_NAME, ORBIT_REGION

CONTAINER = 'pwagner/elasticsearch-aws'
SERVICE_NAME = 'elasticsearch.service'
SERVICE_NAME_NO_EXT = 'elasticsearch'


class TestSpaceApp(BaseSpaceAppTest):
    def test_default_regions(self):
        """When no regions are specified, use orbit regions."""
        self.assertEqual({ORBIT_REGION}, self.app.regions.keys())

    def test_custom_regions(self):
        self.app = SpaceApp(self.orbit, APP_NAME, [ORBIT_REGION, 'meow'])
        self.assertEqual({ORBIT_REGION}, self.app.regions.keys())

    def test_valid(self):
        self.assertTrue(self.app.valid)

    def test_valid_no_name(self):
        self.app.name = None
        self.assertFalse(self.app.valid)

    def test_valid_no_regions(self):
        self.app.regions = ()
        self.assertFalse(self.app.valid)

    def test_full_name(self):
        self.assertEquals(self.app.full_name, 'test-orbit-test-app')


class TestSpaceServicePort(BaseSpaceAppTest):
    def test_port_443_http(self):
        port = SpaceServicePort(port=443)
        self.assertEquals('HTTPS', port.scheme)
