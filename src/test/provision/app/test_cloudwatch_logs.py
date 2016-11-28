from spacel.provision.app.cloudwatch_logs import CloudWatchLogsDecorator

from test.provision.app.test_base_decorator import BaseTemplateDecoratorTest

RETENTION = 7


class TestCloudWatchLogsDecorator(BaseTemplateDecoratorTest):
    def setUp(self):
        super(TestCloudWatchLogsDecorator, self).setUp()
        self.log_iam_resources = []
        self.resources['WriteLogsPolicy'] = {
            'Properties': {
                'PolicyDocument': {
                    'Statement': [{
                        'Resource': self.log_iam_resources
                    }]
                }
            }
        }
        self.cwl = CloudWatchLogsDecorator()
        self.user_data_params += [
            '{',
            '\"logging\":{',
            '\"deploy\":{}',
            '} }'
        ]
        self.base_resource = len(self.resources)

    def test_logs_noop(self):
        self.cwl.logs(self.app_region, self.resources)
        self.assertEquals(self.base_resource, len(self.resources))

    def test_logs_docker(self):
        self.app_region.logging['docker'] = {
            'retention': RETENTION
        }
        self.cwl.logs(self.app_region, self.resources)

        # LogGroup resource added:
        self.assertEquals(self.base_resource + 1, len(self.resources))
        retention = (self.resources['DockerLogGroup']
                     ['Properties']
                     ['RetentionInDays'])
        self.assertEquals(RETENTION, retention)

        # IAM permission granted:
        self.assertEquals(1, len(self.log_iam_resources))

        # Injected into UserData
        data = self._user_data()
        log_group = (data.get('logging', {})
                     .get('docker', {})
                     .get('group'))
        self.assertEquals('DockerLogGroup', log_group)

    def test_logs_metrics(self):
        self.app_region.logging['docker'] = {
            'retention': RETENTION,
            'metrics': {
                'TestMetric': {
                    'patterns': {
                        '*': '1'
                    }
                }
            }
        }
        self.cwl.logs(self.app_region, self.resources)

        self.assertEquals(self.base_resource + 2, len(self.resources))

        filter_properties = (self.resources['TestMetricMetricFilterSTAR']
                             ['Properties'])
        self.assertEquals('*', filter_properties['FilterPattern'])
