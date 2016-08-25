import logging

from spacel.provision.alarm.alert.email import EmailAlerts
from spacel.provision.alarm.alert.pagerduty import PagerDutyAlerts
from spacel.provision.alarm.alert.slack import SlackAlerts

logger = logging.getLogger('spacel.provision.alarms.alerts.factory')


class AlertFactory(object):
    def __init__(self, factories):
        self._factories = factories

    def add_alerts(self, template, alerts):
        alert_resources = {}

        logger.debug('Injecting %d alerts.', len(alerts))
        for name, params in alerts.items():
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
            else:
                logger.debug('Alert %s was invalid.', name)
        logger.debug('Built alerts: %s', alert_resources)
        return alert_resources

    @staticmethod
    def get(pagerduty_default, lambda_uploader):
        return AlertFactory({
            'email': EmailAlerts(),
            'pagerduty': PagerDutyAlerts(pagerduty_default),
            'slack': SlackAlerts(lambda_uploader)
        })
