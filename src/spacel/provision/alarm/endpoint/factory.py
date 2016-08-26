import logging

from spacel.provision.alarm.endpoint.email import EmailEndpoints
from spacel.provision.alarm.endpoint.pagerduty import PagerDutyEndpoints
from spacel.provision.alarm.endpoint.scale import ScaleEndpoints
from spacel.provision.alarm.endpoint.slack import SlackEndpoints

logger = logging.getLogger('spacel.provision.alarm.endpoint.factory')


class AlarmEndpointFactory(object):
    def __init__(self, factories):
        self._factories = factories

    def add_endpoints(self, template, endpoints):
        endpoint_resources = {}

        logger.debug('Injecting %d endpoints.', len(endpoints))
        for name, params in endpoints.items():
            endpoint_type = params.get('type')
            if not endpoint_type:
                logger.warn('Endpoint %s is missing "type".', name)
                continue

            factory = self._factories.get(endpoint_type)
            if not factory:
                logger.warn('Endpoint %s has invalid "type". Valid types: %s',
                            name, sorted(self._factories.keys()))
                continue

            actions = factory.add_endpoints(template, name, params)
            if actions:
                endpoint_resources[name] = {
                    'name': factory.resource_name(name),
                    'actions': actions
                }
            else:
                logger.debug('Endpoint %s was invalid.', name)
        logger.debug('Built endpoints: %s', endpoint_resources)
        return endpoint_resources

    @staticmethod
    def get(pagerduty_default, lambda_uploader):
        return AlarmEndpointFactory({
            'email': EmailEndpoints(),
            'pagerduty': PagerDutyEndpoints(pagerduty_default),
            'slack': SlackEndpoints(lambda_uploader),
            'scale': ScaleEndpoints(),
            'scaledown': ScaleEndpoints(direction=-1),
            'scaleup': ScaleEndpoints(direction=1)
        })
