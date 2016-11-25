from mock import MagicMock

from spacel.provision.app.ingress_resource import IngressResourceFactory
from test.provision.app.test_base_decorator import BaseTemplateDecoratorTest


class BaseDbTest(BaseTemplateDecoratorTest):
    def setUp(self):
        super(BaseDbTest, self).setUp()
        self.ingress = MagicMock(spec=IngressResourceFactory)
