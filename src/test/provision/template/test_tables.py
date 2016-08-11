import unittest

from spacel.model import Orbit
from spacel.provision.template.tables import TablesTemplate

REGION = 'us-east-1'


class TestTablesTemplate(unittest.TestCase):
    def setUp(self):
        self.cache = TablesTemplate()
        base_template = self.cache.get('tables')
        self.base_resources = len(base_template['Resources'])
        self.orbit = Orbit({})

    def test_tables(self):
        tables = self.cache.tables(self.orbit)

        table_resources = len(tables['Resources'])
        self.assertEquals(self.base_resources, table_resources)
