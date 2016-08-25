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
        endpoints = self.endpoint.add_endpoints(self.template, RESOURCE_NAME,
                                                {})
        self.assertFalse(endpoints)
        self.assertEquals(0, len(self.resources))

    def test_add_endpoints(self):
        endpoints = self.endpoint.add_endpoints(self.template, RESOURCE_NAME,
                                                {})
        self.assertTrue(endpoints)
        self.assertEquals(1, len(self.resources))
        self.assertIn(self.topic_resource(), self.resources)
        self.assertEquals(1, len(self.subscriptions()))
