import unittest

from spacel.model.service import SpaceService, SpaceDockerService
from test.model.test_app import SERVICE_NAME, CONTAINER

VERSION = '1.0.0'
UNIT_FILE = '__VERSION__'
VERSIONED_CONTAINER = 'foo:1.2.3'


class TestSpaceService(unittest.TestCase):
    def test_unit_file_no_version(self):
        service = SpaceService(SERVICE_NAME, UNIT_FILE)
        self.assertEquals('latest', service.unit_file)

    def test_unit_file_version(self):
        service = SpaceService(SERVICE_NAME, UNIT_FILE, version=VERSION)
        self.assertEquals(VERSION, service.unit_file)

    def test_unit_file_setter(self):
        service = SpaceService(SERVICE_NAME, None)
        service.unit_file = UNIT_FILE
        self.assertEquals('latest', service.unit_file)


class TestSpaceDockerService(unittest.TestCase):
    def test_constructor_ports(self):
        service = SpaceDockerService(SERVICE_NAME,
                                     CONTAINER,
                                     ports={
                                         9200: 9200,
                                         9300: 9300
                                     })
        self.assertIn('-p 9200:9200', service.unit_file)
        self.assertIn('-p 9300:9300', service.unit_file)
        self.assertIn(' %s' % CONTAINER, service.unit_file)
        self.assertIn('elasticsearch.service', service.name)

    def test_unit_file_no_version(self):
        service = SpaceDockerService(SERVICE_NAME, CONTAINER)
        self.assertIn('%s:latest' % CONTAINER, service.unit_file)

    def test_unit_file_version(self):
        service = SpaceDockerService(SERVICE_NAME, CONTAINER, version=VERSION)
        self.assertIn('%s:%s' % (CONTAINER, VERSION), service.unit_file)

    def test_unit_file_version_locked(self):
        service = SpaceDockerService(SERVICE_NAME, VERSIONED_CONTAINER,
                                     version=VERSION)
        self.assertNotIn(VERSION, service.unit_file)
        self.assertIn(VERSIONED_CONTAINER, service.unit_file)
