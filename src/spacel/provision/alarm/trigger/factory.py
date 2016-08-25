import logging
import re
from spacel.provision import clean_name
from spacel.provision.alarm.trigger.metrics import MetricDefinitions

logger = logging.getLogger('spacel.provision.alarm.trigger.factory')


class TriggerFactory(object):
    def __init__(self):
        self._metrics = MetricDefinitions()

    def add_triggers(self, template, triggers, endpoint_resources):
        for name, params in triggers.items():
            endpoints = self._get_endpoints(params)
            if not endpoints:
                logger.warn('Trigger %s is missing "endpoints".', name)
                continue

            endpoint_actions = self._get_endpoint_actions(endpoints,
                                                          endpoint_resources,
                                                          name)
            if not endpoint_actions:
                logger.warn('Trigger %s has no valid "endpoints".', name)
                continue

            metric = params.get('metric')
            if not metric:
                logger.warn('Trigger %s is missing "metric".', name)
                continue

            defaults = self._metrics.get(metric)
            if not defaults:
                logger.warn('Trigger %s has invalid "metric".', name)
                continue

            threshold_raw = self._get_param(params, defaults, 'threshold')
            operator, thresh = self._parse_threshold(threshold_raw)
            if not operator or thresh is None:
                logger.warn('Trigger %s has invalid "threshold".', name)
                continue

            period_raw = self._get_param(params, defaults, 'period')
            periods, period = self._parse_period(period_raw)
            if not periods or not period:
                logger.warn('Trigger %s has invalid "period".', name)
                continue

            alarm_description = 'Alarm %s' % name
            alarm_stat = self._get_param(params, defaults, 'statistic')

            trigger_name = 'Alarm%s' % clean_name(name)
            resources = template['Resources']
            alarm_properties = {
                'ActionsEnabled': 'true',
                'AlarmDescription': alarm_description,
                'Namespace': defaults['namespace'],
                'MetricName': defaults['metricName'],
                'ComparisonOperator': operator,
                'EvaluationPeriods': periods,
                'Period': period,
                'Statistic': alarm_stat,
                'Threshold': thresh,
                'AlarmActions': endpoint_actions,
                'OKActions': endpoint_actions
            }

            dimensions = defaults.get('dimensions')
            if dimensions:
                alarm_properties['Dimensions'] = dimensions

            resources[trigger_name] = {
                'Type': 'AWS::CloudWatch::Alarm',
                'Properties': alarm_properties
            }

    @staticmethod
    def _get_param(params, defaults, key):
        threshold_raw = params.get(key, defaults.get(key))
        return threshold_raw

    @staticmethod
    def _get_endpoints(params):
        endpoints = params.get('endpoints')
        if isinstance(endpoints, str):
            endpoints = (endpoints,)
        return endpoints

    @staticmethod
    def _get_endpoint_actions(endpoints, endpoint_resources, name):
        endpoint_actions = []
        for endpoint in endpoints:
            endpont_resource = endpoint_resources.get(endpoint)
            if not endpont_resource:
                logger.warn('Trigger %s has invalid "endpoints": %s',
                            name, endpoint)
                continue
            endpoint_actions.append({'Ref': endpont_resource})
        return endpoint_actions

    @staticmethod
    def _parse_threshold(threshold):
        if not threshold:
            return None, None
        match = re.match('([=><]+)([0-9]+)', threshold)
        if not match:
            logger.warn('Invalid threshold %s', threshold)
            return None, None

        op = match.group(1)
        value = int(match.group(2))

        if op == '>':
            return 'GreaterThanThreshold', value
        elif op == '>=':
            return 'GreaterThanOrEqualToThreshold', value
        elif op == '<':
            return 'LessThanThreshold', value
        elif op == '<=':
            return 'LessThanOrEqualToThreshold', value
        else:
            logger.warn('Invalid threshold operator %s', op)
            return None, None

    @staticmethod
    def _parse_period(period_raw):
        if not period_raw or 'x' not in period_raw:
            return None, None
        periods, period = period_raw.split('x', 2)
        try:
            period = int(period)
            if period < 30:
                periods, period = period, int(periods)
            if period % 60 != 0:
                period = int(round(float(period) / 60)) * 60
                logger.warn(
                    'Alarm periods must be multiples of 60, rounded to %ss',
                    period)
            return int(periods), period
        except:
            logger.warn('Invalid alarm period %s', period_raw)
        return None, None
