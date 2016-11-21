import logging
import re

from spacel.provision import clean_name
from spacel.provision.app.alarm.actions import (ACTION_ALARM,
                                                ACTION_INSUFFICIENT_DATA,
                                                ACTION_OK)

logger = logging.getLogger('spacel.provision.app.alarm.trigger')


class BaseTriggerFactory(object):
    def _build_alarm(self, name, params, endpoint_resources, resources,
                     custom_namespace=True, resource_name=''):
        metric = params.get('metric')
        if not metric:
            logger.warning('Trigger %s is missing "metric".', name)
            return None

        defaults = self._get_defaults(resource_name, metric)
        if not defaults:
            namespace = params.get('namespace')
            if not namespace or not custom_namespace:
                logger.warning('Trigger %s has invalid "metric".', name)
                return None
            defaults = {
                'namespace': namespace,
                'metricName': metric,
                'dimensions': params.get('dimensions')
            }

        endpoints = self._get_endpoints(params)
        if not endpoints:
            logger.warning('Trigger %s is missing "endpoints".', name)
            return None

        alarm, insufficient, ok = self._get_endpoint_actions(endpoints,
                                                             endpoint_resources,
                                                             name)
        if not alarm and not insufficient and not ok:
            logger.warning('Trigger %s has no valid "endpoints".', name)
            return None

        threshold_raw = self._get_param(params, defaults, 'threshold')
        operator, thresh = self._parse_threshold(threshold_raw)
        if not operator or thresh is None:
            logger.warning('Trigger %s has invalid "threshold".', name)
            return None

        period_raw = self._get_param(params, defaults, 'period')
        periods, period = self._parse_period(period_raw)
        if not periods or not period:
            logger.warning('Trigger %s has invalid "period".', name)
            return None

        alarm_description = 'Alarm %s' % name
        alarm_stat = self._get_param(params, defaults, 'statistic')
        if not alarm_stat:
            logger.warning('Trigger %s has invalid "statistic".', name)
            return None

        alarm_properties = {
            'ActionsEnabled': 'true',
            'AlarmDescription': alarm_description,
            'Namespace': defaults['namespace'],
            'MetricName': defaults['metricName'],
            'ComparisonOperator': operator,
            'EvaluationPeriods': periods,
            'Period': period,
            'Statistic': alarm_stat,
            'Threshold': thresh
        }
        if alarm:
            alarm_properties['AlarmActions'] = alarm
        if insufficient:
            alarm_properties['InsufficientDataActions'] = insufficient
        if ok:
            alarm_properties['OKActions'] = ok
        dimensions = defaults.get('dimensions')
        if dimensions:
            alarm_properties['Dimensions'] = [
                {'Name': k, 'Value': v}
                for k, v in dimensions.items()]

        trigger_name = 'Alarm%s%s' % (resource_name, clean_name(name))
        resources[trigger_name] = {
            'Type': 'AWS::CloudWatch::Alarm',
            'Properties': alarm_properties
        }

    def _get_defaults(self, name, metric):
        return None

    @staticmethod
    def _get_param(params, defaults, key):
        return params.get(key, defaults.get(key))

    @staticmethod
    def _get_endpoints(params):
        endpoints = params.get('endpoints')
        if isinstance(endpoints, str):
            endpoints = (endpoints,)
        return endpoints

    @staticmethod
    def _get_endpoint_actions(endpoints, endpoint_resources, name):
        alarm = []
        insufficient_data = []
        ok = []

        for endpoint in endpoints:
            endpoint_resource = endpoint_resources.get(endpoint)
            if not endpoint_resource:
                logger.warning('Trigger %s has invalid "endpoints": %s',
                               name, endpoint)
                continue
            resource_ref = {'Ref': endpoint_resource['name']}

            resource_actions = set(endpoint_resource['actions'])
            if ACTION_ALARM in resource_actions:
                alarm.append(resource_ref)
            if ACTION_INSUFFICIENT_DATA in resource_actions:
                insufficient_data.append(resource_ref)
            if ACTION_OK in resource_actions:
                ok.append(resource_ref)
        return alarm, insufficient_data, ok

    @staticmethod
    def _parse_threshold(threshold):
        if not threshold:
            return None, None
        match = re.match('([=><]+)([0-9.]+)', threshold)
        if not match:
            logger.warning('Invalid threshold %s', threshold)
            return None, None

        op = match.group(1)
        value = float(match.group(2))

        if op == '>':
            return 'GreaterThanThreshold', value
        elif op == '>=':
            return 'GreaterThanOrEqualToThreshold', value
        elif op == '<':
            return 'LessThanThreshold', value
        elif op == '<=':
            return 'LessThanOrEqualToThreshold', value
        else:
            logger.warning('Invalid threshold operator %s', op)
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
                logger.warning(
                    'Alarm periods must be multiples of 60, rounded to %ss',
                    period)
            return int(periods), period
        except:
            logger.warning('Invalid alarm period %s', period_raw)
        return None, None
