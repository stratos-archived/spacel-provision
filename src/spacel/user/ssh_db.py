import logging

from spacel.model import SpaceApp

logger = logging.getLogger('spacel.user.ssh_db')

EXPRESSION_ARGS = ('ExpressionAttributeNames', 'ExpressionAttributeValues')


class SpaceSshDb(object):
    def __init__(self, clients):
        self._clients = clients

    def add_key(self, orbit, user_name, key):
        """
        Register key for user in orbit.
        :param orbit:  Orbit.
        :param user_name:  User name.
        :param key: SSH public key.
        """
        self._update_user_keys(orbit, user_name, 'ADD #field :keys', key)

    def remove_key(self, orbit, user_name, key):
        """
        Remove key from user in orbit.
        :param orbit:  Orbit.
        :param user_name:  Username.
        :param key: SSH public key.
        """
        self._update_user_keys(orbit, user_name, 'DELETE #field :keys', key)

    def remove_keys(self, orbit, user_name):
        """
        Remove ALL keys for user in orbit.
        :param orbit: Orbit.
        :param user_name: Username.
        """
        self._update_user_keys(orbit, user_name, 'REMOVE #field')

    def _update_user_keys(self, orbit, user_name, expression, key=None):
        table_name = '%s-users' % orbit.name
        for region in orbit.regions:
            dynamodb = self._clients.dynamodb(region)
            update_args = {
                'TableName': table_name,
                'Key': {'username': {'S': user_name}},
                'UpdateExpression': expression,
                'ExpressionAttributeNames': {'#field': 'keys'}
            }
            if key:
                update_args['ExpressionAttributeValues'] = {
                    ':keys': {'SS': [key]}
                }
            dynamodb.update_item(**update_args)

    def grant(self, app, user_name):
        """
        Grant a user access to an application.
        :param app: Space App.
        :param user_name: User name.
        """
        self._update_service_users(app, 'ADD admins :admins', user_name)

    def revoke(self, app, user_name):
        """
        Revoke access to an application for a user.
        :param app: Space App.
        :param user_name:  User name.
        """
        self._update_service_users(app, 'DELETE admins :admins', user_name)

    def _update_service_users(self, app, expression, user_name):
        table_name = self._services_table(app.orbit)
        for region in app.regions:
            dynamodb = self._clients.dynamodb(region)

            update_args = {
                'TableName': table_name,
                'Key': {'name': {'S': app.name}},
                'UpdateExpression': expression,
            }
            if user_name:
                update_args['ExpressionAttributeValues'] = {
                    ':admins': {'SS': [user_name]}
                }

            dynamodb.update_item(**update_args)

    def revoke_all(self, orbit, user_name):
        """
        Revoke all access to applications for a user.
        :param orbit: Orbit.
        :param user_name: User name.
        :return:
        """
        table_name = self._services_table(orbit)
        scan_filter = {'admins': {
            'AttributeValueList': [{'S': user_name}],
            'ComparisonOperator': 'CONTAINS'
        }}
        for region in orbit.regions:
            dynamodb = self._clients.dynamodb(region)

            # Scan for services this user has permission to:
            scanner = dynamodb.get_paginator('scan').paginate(
                TableName=table_name,
                AttributesToGet=('name',),
                ScanFilter=scan_filter
            )
            for scan_page in scanner:
                # Delete user for each app:
                for service_item in scan_page['Items']:
                    app = SpaceApp(orbit)
                    app.name = service_item['name']['S']
                    try:
                        self._update_service_users(app, 'DELETE admins :admins',
                                                   user_name)
                    except:
                        continue

    @staticmethod
    def _services_table(orbit):
        return '%s-services' % orbit.name
