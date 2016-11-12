import logging

logger = logging.getLogger('spacel.provision.app.db')


class BaseTemplateDecorator(object):
    def __init__(self, ingress):
        self._ingress = ingress

    def _add_client_resources(self, resources, app, region, port, params,
                              sg_ref):
        clients = params.get('clients', ())
        ingress_resources = self._ingress.ingress_resources(app.orbit,
                                                            region,
                                                            port,
                                                            clients,
                                                            sg_ref=sg_ref)
        logger.debug('Adding %s ingress rules.', len(ingress_resources))
        resources.update(ingress_resources)

    @staticmethod
    def _user_data(resources):
        return (resources['Lc']
                ['Properties']
                ['UserData']
                ['Fn::Base64']
                ['Fn::Join'][1])
