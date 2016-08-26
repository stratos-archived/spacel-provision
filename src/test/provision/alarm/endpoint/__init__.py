import unittest

RESOURCE_NAME = 'Test_Resource'


class BaseEndpointTest(unittest.TestCase):
    def setUp(self):
        self.endpoint = None
        self.resources = {}
        self.template = {
            'Resources': self.resources
        }

    def test_resource_name(self):
        if self.endpoint:
            resource_name = self.endpoint.resource_name(RESOURCE_NAME)
            self.assertEquals(self.topic_resource(), resource_name)

    def subscriptions(self):
        resource_name = self.topic_resource()
        return self.resources[resource_name]['Properties']['Subscription']

    def topic_resource(self):
        raise ValueError('Must override topic_resource.')
