from spacel.provision.alarm.endpoint.pagerduty import PagerDutyEndpoints
from test.provision.alarm.endpoint import RESOURCE_NAME, BaseEndpointTest

DEFAULT_URL = 'https://api.pagerduty.com/hook'


class TestPagerDutyEndpoints(BaseEndpointTest):
    def setUp(self):
        super(TestPagerDutyEndpoints, self).setUp()
        self.endpoint = PagerDutyEndpoints(DEFAULT_URL)

    def topic_resource(self):
        return 'EndpointPagerDutyTestResourceTopic'

    def test_add_endpoints_invalid(self):
        self.endpoint = PagerDutyEndpoints(None)
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {})
        self.assertEquals(0, len(actions))
        self.assertEquals(0, len(self.resources))

    def test_add_endpoints(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {})
        self.assertNotEquals(0, len(actions))
        self.assertEquals(1, len(self.resources))
        self.assertIn(self.topic_resource(), self.resources)
        self.assertEquals(1, len(self.subscriptions()))
