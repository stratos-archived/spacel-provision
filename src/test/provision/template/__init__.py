from mock import MagicMock

from spacel.aws import AmiFinder
from test import BaseSpaceAppTest

SUBNET_1 = 'subnet-000001'
SUBNET_2 = 'subnet-000002'
SUBNET_3 = 'subnet-000003'
SUBNETS = (SUBNET_1, SUBNET_2, SUBNET_3)


class BaseTemplateTest(BaseSpaceAppTest):
    def setUp(self):
        super(BaseTemplateTest, self).setUp()
        self.ami_finder = MagicMock(spec=AmiFinder)
        self.cache = self._cache(self.ami_finder)

        # Track the number of resources in the template before any injection:
        if self._template_name():
            base_template = self.cache.get(self._template_name())
            self.base_resources = len(base_template['Resources'])
        else:
            self.base_resources = 0

    def _template_name(self):
        return None

    def _cache(self, ami_finder):
        return None
