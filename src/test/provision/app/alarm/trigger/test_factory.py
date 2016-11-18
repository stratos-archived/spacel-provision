import unittest

from spacel.provision.app.alarm.actions import ACTIONS_ALL, ACTION_ALARM
from spacel.provision.app.alarm.trigger.factory import TriggerFactory

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

    def _add_triggers(self):
        self.factory.add_triggers(self.template, {
            'test': self.params
        }, self.endpoint_resources)
