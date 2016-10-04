import logging

logger = logging.getLogger('spacel.provision.alarm.endpoint.factory')


class AlarmEndpointFactory(object):
    def __init__(self, factories):
        self._factories = factories

    def add_endpoints(self, template, endpoints):
        endpoint_resources = {}

        logger.debug('Injecting %d endpoints.', len(endpoints))
        for name, params in endpoints.items():
            factory = self._factory_for_type(params, name)
            if not factory:
                continue

            actions = factory.add_endpoints(template, name, params)
            if actions:
                endpoint_resources[name] = {
                    'name': factory.resource_name(name),
                    'actions': actions
                }
            else:
                logger.debug('Endpoint %s was invalid.', name)
        if endpoint_resources:
            logger.debug('Built endpoints: %s', endpoint_resources)
        return endpoint_resources

    def _factory_for_type(self, params, name):
        endpoint_type = params.get('type')
        if not endpoint_type:
            logger.warning('Endpoint %s is missing "type".', name)
            return None

        factory = self._factories.get(endpoint_type)
        if not factory:
            logger.warning('Endpoint %s has invalid "type". Valid types: %s',
                           name, sorted(self._factories.keys()))
            return None
        return factory
