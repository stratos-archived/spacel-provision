from spacel.provision.template.base import BaseTemplateCache


class TablesTemplate(BaseTemplateCache):
    def __init__(self, template_cache, ami_finder):
        super(TablesTemplate, self).__init__(template_cache, ami_finder)

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
