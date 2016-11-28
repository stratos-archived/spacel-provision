from spacel.provision.app.cloudwatch_logs_alarm import \
    CloudWatchLogsTriggerFactory

from test import BaseSpaceAppTest, ORBIT_NAME, APP_NAME

NAMESPACE = 'LogMetrics/%s/%s' % (APP_NAME, ORBIT_NAME)
ENDPOINT = 'test'


class TestCloudWatchLogsTriggerFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestCloudWatchLogsTriggerFactory, self).setUp()
        self.factory = CloudWatchLogsTriggerFactory(NAMESPACE)
        self.resources = {}
        self.params = {
            'TestAlarm': {
                'endpoints': [ENDPOINT],
                'threshold': '>10',
                'period': '3x60'
            }
        }
        self.app_region.alarm_endpoints = {
            ENDPOINT: {
                'name': 'SomeTopic',
                'actions': ('Ok', 'Alarm')
            }
        }

    def test_add_alarms_noop(self):
        del self.app_region.alarm_endpoints[ENDPOINT]

        self.factory.add_cloudwatch_alarm(self.app_region, self.resources,
                                          'LogMetric', self.params)
        self.assertEquals({}, self.resources)

    def test_add_alarms(self):
        self.factory.add_cloudwatch_alarm(self.app_region, self.resources,
                                          'LogMetric', self.params)
        alarm = self.resources['AlarmTestAlarm']['Properties']
        self.assertEquals(NAMESPACE, alarm['Namespace'])
