from spacel.provision.template.vpc import VpcTemplate
from test.provision.template import BaseTemplateTest


class TestVpcTemplate(BaseTemplateTest):
    def _template_name(self):
        return 'vpc'

    def _cache(self, ami_finder):
        return VpcTemplate()

    def test_vpc_no_az(self):
        self.orbit_region.az_keys = []
        vpc = self.cache.vpc(self.orbit_region)

        # No resources injected:
        self.assertEquals(self.base_resources, len(vpc['Resources']))

    def test_vpc_no_private_nat_gateway(self):
        self.orbit_region.private_nat_gateway = 'disabled'
        vpc = self.cache.vpc(self.orbit_region)

        # No nat gateway injected
        vpc_resources = vpc['Resources']

        self.assertNotIn('NatGateway01', vpc_resources)

    def test_vpc(self):
        self.vpc_regions('us-east-1a', 'us-east-1b')
        self.vpc_regions('us-east-1a', 'us-east-1b', 'us-east-1c')
        self.vpc_regions('us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d')

    def vpc_regions(self, *args):
        self.orbit_region.az_keys = args
        vpc = self.cache.vpc(self.orbit_region)
        # For N AZs, N-1 resources are injected:
        injected_resources = len(vpc['Resources']) - self.base_resources
        self.assertEquals(0, injected_resources % (len(args) - 1))
