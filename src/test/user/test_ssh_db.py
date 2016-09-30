from mock import MagicMock, ANY
from botocore.exceptions import ClientError

from spacel.aws import ClientCache
from spacel.user.ssh_db import SpaceSshDb
from test import BaseSpaceAppTest

USER_NAME = 'test-user'
KEY = 'ssh-rsa fake123'
USERS_TABLE = 'test-orbit-users'
SERVICES_TABLE = 'test-orbit-services'


class TestSShDb(BaseSpaceAppTest):
    def setUp(self):
        super(TestSShDb, self).setUp()
        self.dynamo = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{
            'Items': [
                {'name': {'S': 'service1'}},
                {'name': {'S': 'service2'}}
            ]
        }]
        self.dynamo.get_paginator.return_value = paginator

        self.clients = MagicMock(spec=ClientCache)
        self.clients.dynamodb.return_value = self.dynamo
        self.ssh_db = SpaceSshDb(self.clients)

    def test_add_key(self):
        self.ssh_db.add_key(self.orbit, USER_NAME, KEY)
        self.dynamo.update_item.assert_called_with(
            TableName=USERS_TABLE,
            Key={'username': {'S': USER_NAME}},
            UpdateExpression='ADD #field :keys',
            ExpressionAttributeValues={':keys': {'SS': [KEY]}},
            ExpressionAttributeNames=ANY
        )

    def test_remove_key(self):
        self.ssh_db.remove_key(self.orbit, USER_NAME, KEY)
        self.dynamo.update_item.assert_called_with(
            TableName=USERS_TABLE,
            Key={'username': {'S': USER_NAME}},
            UpdateExpression='DELETE #field :keys',
            ExpressionAttributeValues={':keys': {'SS': [KEY]}},
            ExpressionAttributeNames=ANY
        )

    def test_remove_keys(self):
        self.ssh_db.remove_keys(self.orbit, USER_NAME)

        self.dynamo.update_item.assert_called_with(
            TableName=USERS_TABLE,
            Key={'username': {'S': USER_NAME}},
            UpdateExpression='REMOVE #field',
            ExpressionAttributeNames=ANY
        )

    def test_grant(self):
        self.ssh_db.grant(self.app, USER_NAME)
        self.dynamo.update_item.assert_called_with(
            TableName=SERVICES_TABLE,
            Key={'name': {'S': self.app.name}},
            UpdateExpression='ADD admins :admins',
            ExpressionAttributeValues={':admins': {'SS': [USER_NAME]}}
        )

    def test_revoke(self):
        self.ssh_db.revoke(self.app, USER_NAME)
        self.dynamo.update_item.assert_called_with(
            TableName=SERVICES_TABLE,
            Key={'name': {'S': self.app.name}},
            UpdateExpression='DELETE admins :admins',
            ExpressionAttributeValues={':admins': {'SS': [USER_NAME]}}
        )

    def test_revoke_all(self):
        self.ssh_db.revoke_all(self.orbit, USER_NAME)
        self.assertEquals(2, self.dynamo.update_item.call_count)

    def test_revoke_all_skip_exception(self):
        self.dynamo.update_item.side_effect = [
            ClientError({'Error': {'Message': 'Kaboom'}}, 'UpdateItem'),
            None
        ]

        self.ssh_db.revoke_all(self.orbit, USER_NAME)
        self.assertEquals(2, self.dynamo.update_item.call_count)
