from spacel.provision.app.alarm.endpoint.email import EmailEndpoints
from test.provision.app.alarm.endpoint import RESOURCE_NAME, BaseEndpointTest


class TestEmailEndpoints(BaseEndpointTest):
    def setUp(self):
        super(TestEmailEndpoints, self).setUp()
        self.endpoint = EmailEndpoints()

    def topic_resource(self):
        return 'EndpointEmailTestResourceTopic'

    def test_add_endpoints_invalid(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {})
        self.assertEquals(0, len(actions))
        self.assertEquals(0, len(self.resources))

    def test_add_endpoints_string(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {
            'addresses': 'test@test.com'
        })
        self.assertNotEquals(0, len(actions))
        self.assertEquals(1, len(self.resources))

        self.assertIn(self.topic_resource(), self.resources)

        subscriptions = self.subscriptions()
        self.assertEquals(1, len(subscriptions))

    def test_add_endpoints_array(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {
            'addresses': ['test@test.com', 'test2@test.com']
        })
        self.assertNotEquals(0, len(actions))
        self.assertEquals(1, len(self.resources))

        subscriptions = self.subscriptions()
        self.assertEquals(2, len(subscriptions))
