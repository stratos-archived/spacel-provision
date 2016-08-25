import unittest

from spacel.provision.alarm.trigger.factory import TriggerFactory

ENDPOINT = 'test'
METRIC = 'cpu'


class TestTriggerFactory(unittest.TestCase):
    def setUp(self):
        self.factory = TriggerFactory()
        self.resources = {}
        self.template = {'Resources': self.resources}
        self.endpoint_resources = {ENDPOINT: 'TestTopic'}

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

    def test_add_triggers(self):
        self._add_triggers()
        self.assertEquals(1, len(self.resources))

    def test_parse_alarm_thresh_missing(self):
        operator, thresh = self.factory._parse_threshold(None)
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_alarm_thresh_invalid(self):
        operator, thresh = self.factory._parse_threshold('meow')
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_alarm_thresh_invalid_operator(self):
        operator, thresh = self.factory._parse_threshold('=1')
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_alarm_thresh_gt(self):
        operator, thresh = self.factory._parse_threshold('>5')
        self.assertEquals(operator, 'GreaterThanThreshold')
        self.assertEquals(thresh, 5)

    def test_parse_alarm_thresh_gte(self):
        operator, thresh = self.factory._parse_threshold('>=0')
        self.assertEquals(operator, 'GreaterThanOrEqualToThreshold')
        self.assertEquals(thresh, 0)

    def test_parse_alarm_thresh_lt(self):
        operator, thresh = self.factory._parse_threshold('<0')
        self.assertEquals(operator, 'LessThanThreshold')
        self.assertEquals(thresh, 0)

    def test_parse_alarm_thresh_lte(self):
        operator, thresh = self.factory._parse_threshold('<=200')
        self.assertEquals(operator, 'LessThanOrEqualToThreshold')
        self.assertEquals(thresh, 200)

    def test_parse_alarm_period_missing(self):
        operator, thresh = self.factory._parse_period(None)
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_alarm_period_invalid(self):
        operator, thresh = self.factory._parse_period('4xmeow')
        self.assertIsNone(operator)
        self.assertIsNone(thresh)

    def test_parse_alarm_period(self):
        periods, period = self.factory._parse_period('3x60')
        self.assertEquals(periods, 3)
        self.assertEquals(period, 60)

    def test_parse_alarm_period_reverse(self):
        periods, period = self.factory._parse_period('300x3')
        self.assertEquals(periods, 3)
        self.assertEquals(period, 300)

    def test_parse_alarm_period_rounding(self):
        periods, period = self.factory._parse_period('3x55')
        self.assertEquals(periods, 3)
        self.assertEquals(period, 60)

    def _add_triggers(self):
        self.factory.add_triggers(self.template, {
            'test': self.params
        }, self.endpoint_resources)
