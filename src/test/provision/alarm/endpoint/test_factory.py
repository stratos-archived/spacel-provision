import unittest
from mock import MagicMock

from spacel.provision.alarm.endpoint.factory import AlarmEndpointFactory

FACTORY_TYPE = 'test'
ENDPOINT_NAME = 'test-endpoint'


class TestAlarmEndpointFactory(unittest.TestCase):
    def setUp(self):
        self.resources = {}
        self.template = {
            'Resources': self.resources
        }
        self.endpoint_factory = MagicMock()
        self.endpoint = AlarmEndpointFactory({
            FACTORY_TYPE: self.endpoint_factory
        })

    def test_add_endpoints_no_type(self):
        self.endpoint.add_endpoints(self.template, {
            ENDPOINT_NAME: {}
        })
        self.endpoint_factory.add_endpoints.assert_not_called()

    def test_add_endpoints_invalid_type(self):
        self.endpoint.add_endpoints(self.template, {
            ENDPOINT_NAME: {
                'type': 'kaboom-missing'
            }
        })
        self.endpoint_factory.add_endpoints.assert_not_called()

    def test_add_endpoints_invalid_endpoint(self):
        self.endpoint_factory.add_endpoints.return_value = False
        endpoints = self.endpoint.add_endpoints(self.template,
                                                {ENDPOINT_NAME: {
                                                    'type': FACTORY_TYPE}})
        self.assertEquals(0, len(endpoints))

    def test_add_endpoints(self):
        params = {'type': FACTORY_TYPE, 'foo': 'bar'}
        endpoints = self.endpoint.add_endpoints(self.template,
                                                {ENDPOINT_NAME: params})
        self.assertEquals(1, len(endpoints))
        self.endpoint_factory.add_endpoints.assert_called_with(self.template,
                                                               ENDPOINT_NAME,
                                                               params)

    def test_get(self):
        endpoint_factory = AlarmEndpointFactory.get(None, None)
        self.assertIsInstance(endpoint_factory, AlarmEndpointFactory)
