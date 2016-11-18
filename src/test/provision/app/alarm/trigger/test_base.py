import unittest

from spacel.provision.app.alarm.trigger.base import BaseTriggerFactory


class TestBaseTriggerFactory(unittest.TestCase):
    def setUp(self):
        self.factory = BaseTriggerFactory()

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

    def test_parse_threshold_decimal(self):
        operator, thresh = self.factory._parse_threshold('<0.3')
        self.assertEquals(operator, 'LessThanThreshold')
        self.assertEquals(thresh, 0.3)

    def test_parse_threshold_ignore_garbage_tail(self):
        operator, thresh = self.factory._parse_threshold('>0.3meow')
        self.assertEquals(operator, 'GreaterThanThreshold')
        self.assertEquals(thresh, 0.3)

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

    def test_get_defaults(self):
        self.assertIsNone(self.factory._get_defaults(None, None))
