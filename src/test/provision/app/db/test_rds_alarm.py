from spacel.provision.app.db.rds_alarm import RdsAlarmTriggerFactory
from test import BaseSpaceAppTest

ENDPOINT = 'test'
METRIC = 'cpu'


class TestRdsAlarmTriggerFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestRdsAlarmTriggerFactory, self).setUp()
        self.factory = RdsAlarmTriggerFactory()
        self.resources = {}
        self.params = {
            'endpoints': [ENDPOINT],
            'metric': METRIC,
            'threshold': '>10',
            'period': '3x60'
        }
        self.app_region.alarm_endpoints = {
            ENDPOINT: {
                'name': 'SomeTopic',
                'actions': ('Ok', 'Alarm')
            }
        }

    def test_cpu_utilization(self):
        alarm = self._add_triggers()
        self.assertEquals('CPUUtilization', alarm['MetricName'])

    def test_cpu_credit_balance(self):
        self.params['metric'] = 'cpu credit balance'
        alarm = self._add_triggers()
        self.assertEquals('CPUCreditBalance', alarm['MetricName'])

    def test_cpu_credit_usage(self):
        self.params['metric'] = 'cpu credit usage'
        alarm = self._add_triggers()
        self.assertEquals('CPUCreditUsage', alarm['MetricName'])

    def test_read_iops(self):
        self.params['metric'] = 'read iops'
        alarm = self._add_triggers()
        self.assertEquals('ReadIOPS', alarm['MetricName'])

    def test_write_latency(self):
        self.params['metric'] = 'writeLatency'
        alarm = self._add_triggers()
        self.assertEquals('WriteLatency', alarm['MetricName'])

    def test_read_throughput(self):
        self.params['metric'] = 'WRITE_THROUGHPUT'
        alarm = self._add_triggers()
        self.assertEquals('WriteThroughput', alarm['MetricName'])

    def test_writes_unknown(self):
        self.params['metric'] = 'writes'
        alarm = self._add_triggers()
        self.assertEquals('WriteIOPS', alarm['MetricName'])

    def _add_triggers(self):
        self.factory.add_rds_alarms(self.app_region, self.resources,
                                    {'test': self.params}, 'DbTest')
        self.assertEquals(1, len(self.resources))
        return self.resources['AlarmDbTesttest']['Properties']
