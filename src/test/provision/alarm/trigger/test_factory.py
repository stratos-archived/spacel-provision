import unittest

from spacel.provision.alarm.actions import ACTIONS_ALL, ACTION_ALARM
from spacel.provision.alarm.trigger.factory import TriggerFactory

ENDPOINT = 'test'
METRIC = 'cpu'


class TestTriggerFactory(unittest.TestCase):
    def setUp(self):
        self.factory = TriggerFactory()
        self.resources = {}
        self.template = {'Resources': self.resources}
        self.endpoint_resources = {ENDPOINT: {
            'name': 'TestTopic',
            'actions': ACTIONS_ALL
        }}

        self.params = {
            'endpoints': [ENDPOINT],
            'metric': METRIC,
            'threshold': '>10',
            'period': '3x60'
        }

    def test_add_triggers_missing_endpoints(self):
        del self.params['endpoints']
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_invalid_endpoints(self):
        self.params['endpoints'] = 'kaboom-missing'
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_missing_metric(self):
        del self.params['metric']
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_invalid_metric(self):
        self.params['metric'] = 'kaboom-invalid'
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_missing_threshold(self):
        self.params['threshold'] = 'kaboom-invalid'
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_missing_period(self):
        self.params['period'] = 'kaboom-invalid'
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_full_custom_invalid(self):
        self.params['namespace'] = 'AWS/SQS'
        self.params['metric'] = 'ApproximateNumberOfMessagesVisible'
        self._add_triggers()
        self.assertEquals(0, len(self.resources))

    def test_add_triggers_full_custom(self):
        self.params['namespace'] = 'AWS/SQS'
        self.params['metric'] = 'ApproximateNumberOfMessagesVisible'
        self.params['dimensions'] = {
            'QueueName': 'test-queue'
        }
        self.params['statistic'] = 'Average'
        self._add_triggers()
        self.assertEquals(1, len(self.resources))
        alarm_params = self.resources['Alarmtest']['Properties']
        self.assertIn('Dimensions', alarm_params)

    def test_add_triggers(self):
        self._add_triggers()
        self.assertEquals(1, len(self.resources))

    def test_get_endpoint_actions_all(self):
        alarm, insufficient_data, ok = self.factory._get_endpoint_actions(
            [ENDPOINT], self.endpoint_resources, 'test')
        self.assertEquals(1, len(alarm))
        self.assertEquals(1, len(insufficient_data))
        self.assertEquals(1, len(ok))

    def test_get_endpoint_actions(self):
        self.endpoint_resources = {ENDPOINT: {
            'name': 'TestTopic',
            'actions': (ACTION_ALARM,)
        }}
        alarm, insufficient_data, ok = self.factory._get_endpoint_actions(
            [ENDPOINT], self.endpoint_resources, 'test')
        self.assertEquals(1, len(alarm))
        self.assertEquals(0, len(insufficient_data))
        self.assertEquals(0, len(ok))

    def test_parse_threshold_missing(self):
        operator, thresh = self.factory._parse_threshold(None)
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_threshold_invalid(self):
        operator, thresh = self.factory._parse_threshold('meow')
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_threshold_invalid_operator(self):
        operator, thresh = self.factory._parse_threshold('=1')
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_threshold_gt(self):
        operator, thresh = self.factory._parse_threshold('>5')
        self.assertEquals(operator, 'GreaterThanThreshold')
        self.assertEquals(thresh, 5)

    def test_parse_threshold_gte(self):
        operator, thresh = self.factory._parse_threshold('>=0')
        self.assertEquals(operator, 'GreaterThanOrEqualToThreshold')
        self.assertEquals(thresh, 0)

    def test_parse_threshold_lt(self):
        operator, thresh = self.factory._parse_threshold('<0')
        self.assertEquals(operator, 'LessThanThreshold')
        self.assertEquals(thresh, 0)

    def test_parse_threshold_lte(self):
        operator, thresh = self.factory._parse_threshold('<=200')
        self.assertEquals(operator, 'LessThanOrEqualToThreshold')
        self.assertEquals(thresh, 200)

    def test_parse_period_missing(self):
        operator, thresh = self.factory._parse_period(None)
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_period_invalid(self):
        operator, thresh = self.factory._parse_period('4xmeow')
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_period(self):
        periods, period = self.factory._parse_period('3x60')
        self.assertEquals(periods, 3)
        self.assertEquals(period, 60)

    def test_parse_period_reverse(self):
        periods, period = self.factory._parse_period('300x3')
        self.assertEquals(periods, 3)
        self.assertEquals(period, 300)

    def test_parse_period_rounding(self):
        periods, period = self.factory._parse_period('3x55')
        self.assertEquals(periods, 3)
        self.assertEquals(period, 60)

    def _add_triggers(self):
        self.factory.add_triggers(self.template, {
            'test': self.params
        }, self.endpoint_resources)
