from spacel.provision.alarm.alert.pagerduty import PagerDutyAlerts
from test.provision.alarm.alert import RESOURCE_NAME, BaseAlertTest

DEFAULT_URL = 'https://api.pagerduty.com/hook'


class TestPagerDutyAlerts(BaseAlertTest):
    def setUp(self):
        super(TestPagerDutyAlerts, self).setUp()
        self.alert = PagerDutyAlerts(DEFAULT_URL)

    def topic_resource(self):
        return 'AlertPagerDutyTestResourceTopic'

    def test_add_alerts_invalid(self):
        self.alert = PagerDutyAlerts(None)
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {})
        self.assertFalse(alerts)
        self.assertEquals(0, len(self.resources))

    def test_add_alerts(self):
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {})
        self.assertTrue(alerts)
        self.assertEquals(1, len(self.resources))
        self.assertIn(self.topic_resource(), self.resources)
        self.assertEquals(1, len(self.subscriptions()))
