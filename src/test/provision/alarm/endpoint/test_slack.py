from mock import MagicMock, ANY

from spacel.provision.lambda_s3 import LambdaUploader
from spacel.provision.alarm.endpoint.slack import SlackEndpoints
from test.provision.alarm.endpoint import RESOURCE_NAME, BaseEndpointTest

URL = 'https://api.slack.com/hook'


class TestSlackEndpoints(BaseEndpointTest):
    def setUp(self):
        super(TestSlackEndpoints, self).setUp()
        self.lambda_uploader = MagicMock(spec=LambdaUploader)
        self.endpoint = SlackEndpoints(self.lambda_uploader)

    def topic_resource(self):
        return 'EndpointSlackTestResourceTopic'

    def test_add_endpoints_invalid(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {})
        self.assertEquals(0, len(actions))
        self.assertEquals(0, len(self.resources))

    def test_add_endpoints(self):
        self.lambda_uploader.upload.return_value = ('bucket', 'key')
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {
            'url': URL
        })
        self.assertNotEquals(0, len(actions))
        self.assertEquals(4, len(self.resources))
        self.assertIn(self.topic_resource(), self.resources)
        self.assertEquals(1, len(self.subscriptions()))

        self.lambda_uploader.upload.assert_called_with(ANY, {
            '__PATH__': '/hook'
        })
