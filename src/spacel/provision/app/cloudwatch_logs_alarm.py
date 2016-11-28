from spacel.provision.app.alarm.trigger.base import BaseTriggerFactory


class CloudWatchLogsTriggerFactory(BaseTriggerFactory):
    """
    Decorates template with Alarm triggers driven by Cloudwatch Log events.
    """

    def __init__(self, namespace):
        super(CloudWatchLogsTriggerFactory, self).__init__()
        self._namespace = namespace

    def add_cloudwatch_alarm(self, app_region, resources, metric_name, alarms):
        for name, params in alarms.items():
            params['metric'] = metric_name
            self._build_alarm(name, params, app_region.alarm_endpoints,
                              resources)

    def _get_defaults(self, name, metric):
        return {
            'namespace': self._namespace,
            'period': '3x60',
            'statistic': 'Sum',
            'metricName': metric
        }
