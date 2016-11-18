import logging

from spacel.provision.app.alarm.trigger.base import BaseTriggerFactory
from spacel.provision.app.alarm.trigger.metrics import MetricDefinitions

logger = logging.getLogger('spacel.provision.app.alarm.trigger.factory')


class TriggerFactory(BaseTriggerFactory):
    def __init__(self):
        self._metrics = MetricDefinitions()

    def add_triggers(self, template, triggers, endpoint_resources):
        for name, params in triggers.items():
            self._build_alarm(name, params, endpoint_resources,
                              template['Resources'])

    def _get_defaults(self, name, metric):
        return self._metrics.get(metric)
