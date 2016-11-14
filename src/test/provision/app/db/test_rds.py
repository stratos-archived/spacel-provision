from botocore.exceptions import ClientError
from mock import MagicMock, ANY

from spacel.aws import ClientCache
from spacel.provision.app.db.rds import RdsFactory
from spacel.security import EncryptedPayload, PasswordManager
from test import REGION
from test.provision.app.db import BaseDbTest
from test.security import CLIENT_ERROR

DB_NAME = 'test-db'
OTHER_REGION = 'us-east-1'
RDS_ID = 'rds-123456'


class TestRdsFactory(BaseDbTest):
    def setUp(self):
        super(TestRdsFactory, self).setUp()
        self.user_data_params += [
            '{',
            '\"databases\":{',
            '} }'
        ]

        self.db_params = {}
        self.app.databases = {
            DB_NAME: self.db_params
        }
        self.app.regions = [REGION, OTHER_REGION]

        self.password_manager = MagicMock(spec=PasswordManager)
        self.password_manager.get_password.return_value = EncryptedPayload(
            b'1234567890123456',
            b'1234567890123456',
            b'1234567890123456',
            'us-east-1',
            'utf-8'
        ), lambda: 'test-password'

        self.clients = MagicMock(spec=ClientCache)
        self.cloudformation = MagicMock()
        self.clients.cloudformation.return_value = self.cloudformation
        self.rds_factory = RdsFactory(self.clients, self.ingress,
                                      self.password_manager)

    def test_add_rds_noop(self):
        self.app.databases = {}
        self.rds_factory.add_rds(self.app, REGION, self.template)

    def test_add_rds_invalid_version(self):
        self.db_params['type'] = 'oracle'
        self.rds_factory.add_rds(self.app, REGION, self.template)
        self.assertEquals(1, len(self.resources))

    def test_add_rds_invalid_port(self):
        self.db_params['port'] = 0
        self.rds_factory.add_rds(self.app, REGION, self.template)
        self.assertEquals(1, len(self.resources))

    def test_add_rds_storage_type(self):
        self.db_params['iops'] = 100
        self.rds_factory.add_rds(self.app, REGION, self.template)
        self.assertEquals(4, len(self.resources))
        db_properties = self.resources['Dbtestdb']['Properties']
        self.assertEquals(100, db_properties['Iops'])
        self.assertEquals('io1', db_properties['StorageType'])

    def test_add_rds_encryption(self):
        self.db_params['encrypted'] = True
        self.rds_factory.add_rds(self.app, REGION, self.template)
        self.assertEquals(4, len(self.resources))
        db_properties = self.resources['Dbtestdb']['Properties']
        self.assertEquals('db.t2.large', db_properties['DBInstanceClass'])

    def test_add_rds_global_other_region_no_db(self):
        self.db_params['global'] = OTHER_REGION
        self.rds_factory._rds_id = MagicMock(return_value=None)

        self.rds_factory.add_rds(self.app, REGION, self.template)

        # DB resource not added, no mention in user data:
        self.assertEquals(1, len(self.resources))
        self.assertNotIn(DB_NAME, self._user_data())

    def test_add_rds_global_other_region_no_password(self):
        self.db_params['global'] = OTHER_REGION
        self.password_manager.get_password.return_value = None, None

        self.rds_factory.add_rds(self.app, REGION, self.template)

        # DB resource not added, no mention in user data:
        self.assertEquals(1, len(self.resources))
        self.assertNotIn(DB_NAME, self._user_data())

    def test_add_rds_global_other_region(self):
        self.db_params['global'] = OTHER_REGION
        self.rds_factory._rds_id = MagicMock(return_value=RDS_ID)

        self.rds_factory.add_rds(self.app, REGION, self.template)

        # DB resource not added, IAM policy is:
        self.assertEquals(2, len(self.resources))
        user_data = self._user_data()
        db_user_data = user_data['databases'][DB_NAME]
        self.assertEquals(RDS_ID, db_user_data['name'])

    def test_add_rds_global_region(self):
        self.db_params['global'] = REGION

        self.rds_factory.add_rds(self.app, REGION, self.template)

        self.assertEquals(4, len(self.resources))
        # Password is saved to other regions:
        self.password_manager.set_password.assert_called_with(self.app,
                                                              OTHER_REGION,
                                                              'rds:test-db',
                                                              ANY)
        self.assertIn(OTHER_REGION, self.db_params['clients'])

    def test_add_rds_global_region_concat(self):
        self.db_params['global'] = REGION
        self.db_params['clients'] = []

        self.rds_factory.add_rds(self.app, REGION, self.template)

        self.assertIn(OTHER_REGION, self.db_params['clients'])

    def test_add_rds(self):
        self.rds_factory.add_rds(self.app, REGION, self.template)
        self.assertEquals(4, len(self.resources))

        # Resolve {'Ref':}s to a string:
        user_data = self._user_data()
        db_user_data = user_data['databases'][DB_NAME]
        self.assertEquals('Dbtestdb', db_user_data['name'])

    def test_instance_type_default(self):
        instance_type = self.rds_factory._instance_type(self.db_params)
        self.assertEquals('db.t2.micro', instance_type)

    def test_instance_type_prefix(self):
        self.db_params['instance_type'] = 't2.small'
        instance_type = self.rds_factory._instance_type(self.db_params)
        self.assertEquals('db.t2.small', instance_type)

    def test_rds_id(self):
        self.cloudformation.describe_stack_resource.return_value = {
            'StackResourceDetail': {
                'PhysicalResourceId': RDS_ID
            }
        }
        rds_id = self.rds_factory._rds_id(self.app, REGION, 'DbTestDb')
        self.assertEquals(RDS_ID, rds_id)

    def test_rds_id_not_found(self):
        self.cloudformation.describe_stack_resource.side_effect = ClientError({
            'Error': {'Message': 'Stack does not exist'}},
            'DescribeStackResource')

        rds_id = self.rds_factory._rds_id(self.app, REGION, 'DbTestDb')
        self.assertIsNone(rds_id)

    def test_rds_id_exception(self):
        self.cloudformation.describe_stack_resource.side_effect = CLIENT_ERROR
        self.assertRaises(ClientError, self.rds_factory._rds_id, self.app,
                          REGION, 'DbTestDb')
