import unittest

from spacel.provision.alarm.trigger.metrics import MetricDefinitions


class TestMetricDefinitions(unittest.TestCase):
    def setUp(self):
        self.metrics = MetricDefinitions()

    def test_get(self):
        cpu_metric = self.metrics.get('cpu')
        self.assertEquals('CPUUtilization', cpu_metric['metricName'])
