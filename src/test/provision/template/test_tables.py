from spacel.provision.template.tables import TablesTemplate
from test import ORBIT_NAME
from test.provision.template import BaseTemplateTest


class TestTablesTemplate(BaseTemplateTest):
    def _template_name(self):
        return 'tables'

    def _cache(self, ami_finder):
        return TablesTemplate()

    def test_tables(self):
        tables = self.cache.tables(self.orbit)

        self.assertEquals(self.base_resources, len(tables['Resources']))

    def test_tables_name(self):
        tables = self.cache.tables(self.orbit)
        orbit_name = tables['Parameters']['Orbit']['Default']
        self.assertEquals(ORBIT_NAME, orbit_name)
