import logging

from spacel.provision import clean_name
from spacel.provision.app.alarm.trigger.base import BaseTriggerFactory

logger = logging.getLogger('spacel.provision.app.db.rds_alarm')


class RdsAlarmTriggerFactory(BaseTriggerFactory):
    def add_rds_alarms(self, app_region, resources, rds_alarms, rds_resource):
        for name, params in rds_alarms.items():
            self._build_alarm(name, params, app_region.alarm_endpoints,
                              resources, resource_name=rds_resource)

    def _get_defaults(self, resource_name, metric):
        """
        Source:
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/rds-metricscollected.html
        """
        rds_dimensions = {
            'DBInstanceIdentifier': {'Ref': resource_name}
        }

        defaults = {
            'namespace': 'AWS/RDS',
            'dimensions': rds_dimensions,
            'period': '3x60',
            'statistic': 'Average'
        }
        metric_lower = clean_name(metric.lower())
        if 'creditusage' in metric_lower:
            defaults['metricName'] = 'CPUCreditUsage'
            defaults['threshold'] = '>10'
            defaults['period'] = '3x300',
        elif 'credit' in metric_lower:
            defaults['metricName'] = 'CPUCreditBalance'
            defaults['threshold'] = '<5'
            defaults['period'] = '3x300',
        elif 'cpu' in metric_lower:
            defaults['metricName'] = 'CPUUtilization'
            defaults['threshold'] = '>50'
        elif 'read' in metric_lower:
            self._io_default('Read', metric_lower, defaults)
        elif 'write' in metric_lower:
            self._io_default('Write', metric_lower, defaults)
        return defaults

    @staticmethod
    def _io_default(rw, metric, defaults):
        if 'latency' in metric:
            defaults['metricName'] = '%sLatency' % rw
            defaults['threshold'] = '>0.5'
        elif 'throughput' in metric:
            defaults['metricName'] = '%sThroughput' % rw
            defaults['threshold'] = '>1000000'
        else:
            defaults['metricName'] = '%sIOPS' % rw
            defaults['threshold'] = '>50'
