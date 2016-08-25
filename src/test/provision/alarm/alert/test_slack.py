from mock import MagicMock, ANY

from spacel.provision.lambda_s3 import LambdaUploader
from spacel.provision.alarm.alert.slack import SlackAlerts
from test.provision.alarm.alert import RESOURCE_NAME, BaseAlertTest

URL = 'https://api.slack.com/hook'


class TestSlackAlerts(BaseAlertTest):
    def setUp(self):
        super(TestSlackAlerts, self).setUp()
        self.lambda_uploader = MagicMock(spec=LambdaUploader)
        self.alert = SlackAlerts(self.lambda_uploader)

    def topic_resource(self):
        return 'AlertSlackTestResourceTopic'

    def test_add_alerts_invalid(self):
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {})
        self.assertFalse(alerts)
        self.assertEquals(0, len(self.resources))

    def test_add_alerts(self):
        self.lambda_uploader.upload.return_value = ('bucket', 'key')
        alerts = self.alert.add_alerts(self.template, RESOURCE_NAME, {
            'url': URL
        })
        self.assertTrue(alerts)
        self.assertEquals(4, len(self.resources))
        self.assertIn(self.topic_resource(), self.resources)
        self.assertEquals(1, len(self.subscriptions()))

        self.lambda_uploader.upload.assert_called_with(ANY, {
            '__PATH__': '/hook'
        })
