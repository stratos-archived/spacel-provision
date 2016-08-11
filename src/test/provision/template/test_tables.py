from mock import MagicMock
import unittest

from spacel.aws import AmiFinder
from spacel.model import Orbit
from spacel.provision.template.tables import TablesTemplate

REGION = 'us-east-1'


class TestTablesTemplate(unittest.TestCase):
    def setUp(self):
        self.ami_finder = MagicMock(spec=AmiFinder)
        self.cache = TablesTemplate({}, self.ami_finder)
        base_template = self.cache.get('tables')
        self.base_resources = len(base_template['Resources'])
        self.orbit = Orbit({})

    def test_tables(self):
        tables = self.cache.tables(self.orbit)

        table_resources = len(tables['Resources'])
        self.assertEquals(self.base_resources, table_resources)
