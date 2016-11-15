import unittest

from spacel.model.service import SpaceDockerService
from test.model.test_app import SERVICE_NAME, CONTAINER


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
