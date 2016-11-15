from spacel.provision.template.bastion import BastionTemplate
from test import ORBIT_DOMAIN
from test.provision.template import BaseTemplateTest


class TestBastionTemplate(BaseTemplateTest):
    def _template_name(self):
        return 'asg-bastion'

    def _cache(self, ami_finder):
        return BastionTemplate(ami_finder)

    def test_bastion_disabled(self):
        self.orbit_region.bastion_instance_count = 0
        bastion = self.cache.bastion(self.orbit_region)
        self.assertIsNone(bastion)

    def test_bastion(self):
        bastion = self.cache.bastion(self.orbit_region)

        # No resources are injected:
        bastion_resources = len(bastion['Resources'])
        self.assertEquals(self.base_resources, bastion_resources)

    def test_bastion_multi_eip(self):
        self.orbit_region.bastion_instance_count = 2
        bastion = self.cache.bastion(self.orbit_region)

        bastion_resources = bastion['Resources']
        # 3 resources: Eip01, DNS:bastion01, DNS:bastion02
        self.assertEquals(self.base_resources + 3, len(bastion_resources))
        self.assertIn('ElasticIp02', bastion_resources)
        self.assertIn('DnsRecord02', bastion_resources)

    def test_bastion_domain(self):
        bastion = self.cache.bastion(self.orbit_region)

        domain = bastion['Parameters']['VirtualHostDomain']['Default']
        self.assertEqual(ORBIT_DOMAIN + '.', domain)
