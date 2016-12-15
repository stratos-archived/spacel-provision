import logging
import uuid


from spacel.provision.cloudformation import BaseCloudFormationFactory

logger = logging.getLogger('spacel')


class SpaceElevatorAppFactory(BaseCloudFormationFactory):
    def __init__(self, clients, change_sets, uploader, app_template):
        super(SpaceElevatorAppFactory, self).__init__(clients, change_sets,
                                                      uploader)
        self._app_template = app_template

    def app(self, app, force_redeploy=False):
        """
        Provision an app in all regions.
        :param app:  App to provision.
        :param force_redeploy: Force redeploying this application.
        :returns True if updates completed.
        """
        app_name = app.full_name
        updates = {}
        unique_token = str(uuid.uuid4())

        params = {}
        if force_redeploy:
            # New token: force redeploy according to UpdatePolicy
            params['UniqueToken'] = unique_token

        for region, app_region in app.regions.items():
            template, secret_params = self._app_template.app(app_region)
            if not template and not secret_params:
                logger.warning('App %s will not be updated, invalid syntax!',
                               app_name)
                continue

            secret_params = secret_params or {}
            # Treat token as a secret: re-use existing value if possible.
            secret_params['UniqueToken'] = lambda: unique_token
            updates[region] = self._stack(app_name, region, template,
                                          parameters=params,
                                          secret_parameters=secret_params)
        return self._wait_for_updates(app_name, updates)

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
