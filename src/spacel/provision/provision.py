import logging

from spacel.provision.cloudformation import BaseCloudFormationFactory

logger = logging.getLogger('spacel')


class CloudProvisioner(BaseCloudFormationFactory):
    def __init__(self, clients, templates):
        self._clients = clients
        self._templates = templates

    def app(self, app):
        app_name = app.full_name
        updates = {}
        for region in app.regions:
            template = self._templates.app(app, region)
            updates[region] = self._stack(app_name, region, template)

        self._wait_for_updates(app_name, updates)
