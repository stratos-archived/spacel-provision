import logging

logger = logging.getLogger('spacel.provision.alarms.alerts.factory')


class AlertFactory(object):
    def __init__(self, factories):
        self._factories = factories

    def add_alerts(self, template, streams):
        alert_resources = {}

        for name, params in streams.items():
            alarm_type = params.get('type')
            if not alarm_type:
                logger.warn('Alert %s is missing "type".', name)
                continue

            alert_factory = self._factories.get(alarm_type)
            if not alert_factory:
                logger.warn('Alert %s has invalid "type". Valid types: %s',
                            name, sorted(self._factories.keys()))
                continue

            valid = alert_factory.add_alerts(template, name, params)
            if valid:
                alert_name = alert_factory.resource_name(name)
                alert_resources[name] = alert_name

        return alert_resources
