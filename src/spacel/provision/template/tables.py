from spacel.provision.template.base import BaseTemplateCache


class TablesTemplate(BaseTemplateCache):
    def __init__(self):
        super(TablesTemplate, self).__init__()

    def tables(self, orbit):
        """
        Get customized template for DynamoDb tables.
        :param orbit: Orbit.
        :return: DynamoDb tables.
        """

        tables_template = self.get('tables')
        params = tables_template['Parameters']
        params['Orbit']['Default'] = orbit.name
        return tables_template
