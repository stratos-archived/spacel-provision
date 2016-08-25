import logging
import re
from spacel.provision import clean_name
from spacel.provision.alarm.trigger.metrics import MetricDefinitions

logger = logging.getLogger('spacel.provision.alarm.trigger.factory')


class TriggerFactory(object):
    def __init__(self):
        self._metrics = MetricDefinitions()

    def add_triggers(self, template, triggers, alarm_resources):
        for name, params in triggers.items():
            alerts = self._get_alerts(params)
            if not alerts:
                logger.warn('Trigger %s is missing "alerts".', name)
                continue

            alarm_actions = self._get_alarm_actions(alerts, alarm_resources,
                                                    name)
            if not alarm_actions:
                logger.warn('Trigger %s has no valid "alerts".', name)
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
            operator, thresh = self._parse_alarm_thresh(threshold_raw)
            if not operator or thresh is None:
                logger.warn('Trigger %s has invalid "threshold".', name)
                continue

            period_raw = self._get_param(params, defaults, 'period')
            periods, period = self._parse_alarm_period(period_raw)
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
                'AlarmActions': alarm_actions,
                'OKActions': alarm_actions
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
    def _get_alerts(params):
        alerts = params.get('alerts')
        if isinstance(alerts, str):
            alerts = (alerts,)
        return alerts

    @staticmethod
    def _get_alarm_actions(alerts, alert_resources, name):
        alarm_actions = []
        for alert in alerts:
            alert_resource = alert_resources.get(alert)
            if not alert_resource:
                logger.warn('Trigger %s has invalid "alerts": %s',
                            name, alert)
                continue
            alarm_actions.append({'Ref': alert_resource})
        return alarm_actions

    @staticmethod
    def _parse_alarm_thresh(threshold):
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
    def _parse_alarm_period(period_raw):
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
