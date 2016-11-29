import logging

from spacel.provision.app.base_decorator import BaseTemplateDecorator

logger = logging.getLogger('spacel.provision.app.db')


class BaseDbTemplateDecorator(BaseTemplateDecorator):
    def __init__(self, ingress):
        super(BaseDbTemplateDecorator, self).__init__()
        self._ingress = ingress

    def _add_client_resources(self, resources, app_region, port, params,
                              sg_ref):
        clients = params.get('clients', ())
        ingress_resources = self._ingress.ingress_resources(app_region,
                                                            port,
                                                            clients,
                                                            sg_ref=sg_ref)
        logger.debug('Adding %s ingress rules.', len(ingress_resources))
        resources.update(ingress_resources)
