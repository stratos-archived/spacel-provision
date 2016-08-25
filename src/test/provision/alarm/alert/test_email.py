from spacel.provision.alarm.alert.email import EmailAlerts
from test.provision.alarm.alert import RESOURCE_NAME, BaseAlertTest


class TestEmailAlerts(BaseAlertTest):
    def setUp(self):
        super(TestEmailAlerts, self).setUp()
        self.alert = EmailAlerts()

    def topic_resource(self):
        return 'AlertEmailTestResourceTopic'

    def test_add_alerts_invalid(self):
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {})
        self.assertFalse(alerts)
        self.assertEquals(0, len(self.resources))

    def test_add_alerts_string(self):
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {
            'addresses': 'test@test.com'
        })
        self.assertTrue(alerts)
        self.assertEquals(1, len(self.resources))

        self.assertIn(self.topic_resource(), self.resources)

        subscriptions = self.subscriptions()
        self.assertEquals(1, len(subscriptions))

    def test_add_alerts_array(self):
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {
            'addresses': ['test@test.com', 'test2@test.com']
        })
        self.assertTrue(alerts)
        self.assertEquals(1, len(self.resources))

        subscriptions = self.subscriptions()
        self.assertEquals(2, len(subscriptions))
