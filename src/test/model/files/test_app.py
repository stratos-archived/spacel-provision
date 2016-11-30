import os
from copy import deepcopy

import six

from spacel.model.files.app import SpaceAppFilesModelFactory
from test import BaseSpaceAppTest, ORBIT_REGION, OTHER_REGION

BASIC_SERVICE = 'ExecStart=/bin/true'
BASIC_ENVIRONMENT = {
    'FOO': 'bar',
    'FOZ': 'baz'
}

OVERRIDE_ENVIRONMENT = deepcopy(BASIC_ENVIRONMENT)
OVERRIDE_ENVIRONMENT.update({
    'FOO': 'baz'
})


class TestSpaceAppFilesModelFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestSpaceAppFilesModelFactory, self).setUp()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.factory = SpaceAppFilesModelFactory(script_dir)

    def test_missing(self):
        app = self.factory.app(self.orbit, 'apps/does-not-exist')
        self.assertIsNone(app)

    def test_systemd(self):
        app = self.factory.app(self.orbit, 'apps/systemd')
        app_region = app.regions[ORBIT_REGION]
        self.assertEquals(1, len(app_region.services))

        test_service = app_region.services['every-region.service']
        self.assertIn(BASIC_SERVICE, test_service.unit_file)
        self.assertEquals(BASIC_ENVIRONMENT, test_service.environment)

        self.assertIn('app-config.txt', app_region.files)

    def test_systemd_multiregion(self):
        self._multi_region()
        app = self.factory.app(self.orbit, 'apps/systemd_multiregion')

        orbit_region = app.regions[ORBIT_REGION]
        other_region = app.regions[OTHER_REGION]

        # Both regions have `every-region`
        orbit_service = orbit_region.services['every-region.service']
        self.assertEquals(BASIC_ENVIRONMENT, orbit_service.environment)
        # us-east-1 overrides a setting:
        other_service = other_region.services['every-region.service']

        self.assertEquals(OVERRIDE_ENVIRONMENT, other_service.environment)

        # Only orbit_region has `orbit-region`
        self.assertIn('orbit-region.service', orbit_region.services)
        self.assertNotIn('orbit-region.service', other_region.services)
        # Only other_region has `other-region`
        self.assertNotIn('other-region.service', orbit_region.services)
        self.assertIn('other-region.service', other_region.services)

        # app-config varies between regions:
        self.assertEquals('global\n', orbit_region.files['app-config.txt'])
        self.assertEquals('us-east-1\n', other_region.files['app-config.txt'])

    def test_mixed_json(self):
        self._multi_region()
        app = self.factory.app(self.orbit, 'apps/mixed')
        orbit_region = app.regions[ORBIT_REGION]
        other_region = app.regions[OTHER_REGION]

        # JSON files are merged to allow regional overrides:
        self.assertEquals('t2.nano', orbit_region.instance_type)
        self.assertEquals('t2.micro', other_region.instance_type)

        # .env files can be added to service from JSON:
        orbit_service = orbit_region.services['laika.service']
        self.assertEquals(BASIC_ENVIRONMENT, orbit_service.environment)
        other_service = other_region.services['laika.service']
        self.assertEquals(OVERRIDE_ENVIRONMENT, other_service.environment)

        # Service can be added:
        self.assertNotIn('other-region.service', orbit_region.services)
        self.assertIn('other-region.service', other_region.services)

    def test_encrypted_payloads(self):
        app = self.factory.app(self.orbit, 'apps/encrypted')
        orbit_region = app.regions[ORBIT_REGION]

        # `valid` is parsed; `invalid` is passed through
        self.assertEquals(2, len(orbit_region.files))
        valid_crypt = orbit_region.files['valid.bin']
        self.assertIsInstance(valid_crypt, dict)
        invalid_crypt = orbit_region.files['invalid.bin.crypt']
        self.assertIsInstance(invalid_crypt, six.string_types)

        # `every-region` is handled as a service (with encrypted .unit_file)
        self.assertEquals(1, len(orbit_region.services))
        every_region = orbit_region.services['every-region.service']
        self.assertIsInstance(every_region.unit_file, dict)
