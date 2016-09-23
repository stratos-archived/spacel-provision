import logging

from spacel.provision.cloudformation import BaseCloudFormationFactory

logger = logging.getLogger('spacel')


class CloudProvisioner(BaseCloudFormationFactory):
    def __init__(self, clients, change_sets, uploader, app):
        super(CloudProvisioner, self).__init__(clients, change_sets, uploader)
        self._app = app

    def app(self, app):
        """
        Provision an app in all regions.
        :param app:  App to provision.
        """
        app_name = app.full_name
        updates = {}
        for region in app.regions:
            template, secret_params = self._app.app(app, region)
            updates[region] = self._stack(app_name, region, template,
                                          secret_parameters=secret_params)
        self._wait_for_updates(app_name, updates)

    def delete_app(self, app):
        """
        Delete an app in all regions.
        :param app:  App to delete.
        """
        app_name = app.full_name
        updates = {}
        for region in app.regions:
            updates[region] = self._delete_stack(app_name, region)
        self._wait_for_updates(app_name, updates)
