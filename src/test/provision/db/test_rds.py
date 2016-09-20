from mock import MagicMock

from spacel.aws import ClientCache
from spacel.provision.db.rds import RdsFactory
from spacel.security import EncryptedPayload, PasswordManager
from test import REGION
from test.provision.db import BaseDbTest

DB_NAME = 'test-db'


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

        self.password_manager = MagicMock(spec=PasswordManager)
        self.password_manager.get_password.return_value = EncryptedPayload(
            b'1234567890123456',
            b'1234567890123456',
            b'1234567890123456',
            'us-east-1',
            'utf-8'
        ), lambda: 'test-password'

        self.clients = MagicMock(spec=ClientCache)
        self.rds_factory = RdsFactory(self.clients, self.ingress,
                                      self.password_manager)

    def test_add_rds_noop(self):
        self.app.databases = {}
        self.rds_factory.add_rds(self.app, REGION, self.template)

    def test_add_rds(self):
        self.rds_factory.add_rds(self.app, REGION, self.template)
        self.assertEquals(3, len(self.resources))

        # Resolve {'Ref':}s to a string:
        user_data = self._user_data()
        db_user_data = user_data['databases'][DB_NAME]
        self.assertEquals('Dbtestdb', db_user_data['name'])
