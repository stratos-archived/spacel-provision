import unittest

RESOURCE_NAME = 'Test_Resource'


class BaseAlertTest(unittest.TestCase):
    def setUp(self):
        self.alert = None
        self.resources = {}
        self.template = {
            'Resources': self.resources
        }

    def test_resource_name(self):
        if self.alert:
            resource_name = self.alert.resource_name(RESOURCE_NAME)
            self.assertEquals(self.topic_resource(), resource_name)

    def subscriptions(self):
        resource_name = self.topic_resource()
        return self.resources[resource_name]['Properties']['Subscription']

    def topic_resource(self):
        raise ValueError('Must override topic_resource.')
