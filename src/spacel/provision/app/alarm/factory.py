from spacel.provision.app.alarm.endpoint.email import EmailEndpoints
from spacel.provision.app.alarm.endpoint.factory import AlarmEndpointFactory
from spacel.provision.app.alarm.endpoint.pagerduty import PagerDutyEndpoints
from spacel.provision.app.alarm.endpoint.scale import ScaleEndpoints
from spacel.provision.app.alarm.endpoint.slack import SlackEndpoints

from spacel.provision.app.alarm.trigger.factory import TriggerFactory


class AlarmFactory(object):
    def __init__(self, endpoints, triggers):
        self._endpoints = endpoints
        self._triggers = triggers

    def add_alarms(self, template, alarms):
        app_endpoints = alarms.get('endpoints', {})
        app_triggers = alarms.get('triggers', {})

        endpoints = self._endpoints.add_endpoints(template, app_endpoints)
        self._triggers.add_triggers(template, app_triggers, endpoints)

    @staticmethod
    def get(pd_default, pd_api_key, lambda_uploader):
        """
        Get alarm factory.
        :param pd_default: PagerDuty default URL.
        :param pd_api_key:  PagerDuty API key.
        :param lambda_uploader: Lambda Uploader.
        """
        endpoints = AlarmEndpointFactory({
            'email': EmailEndpoints(),
            'pagerduty': PagerDutyEndpoints(pd_default, pd_api_key),
            'slack': SlackEndpoints(lambda_uploader),
            'scale': ScaleEndpoints(),
            'scaledown': ScaleEndpoints(direction=-1),
            'scaleup': ScaleEndpoints(direction=1)
        })
        triggers = TriggerFactory()
        return AlarmFactory(endpoints, triggers)
