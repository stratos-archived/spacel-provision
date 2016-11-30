import six
from botocore.exceptions import ClientError
from mock import MagicMock

from spacel.aws import ClientCache
from spacel.provision.app.ingress_resource import (IngressResourceFactory,
                                                   IP_BLOCK)
from test import BaseSpaceAppTest, ORBIT_REGION

OTHER_REGION = 'us-east-1'
PUBLIC_IP_BLOCK = '8.8.8.8/32'
PRIVATE_IP_BLOCK = '192.168.0.0/16'
SECURITY_GROUP = 'sg-123456'
ELASTIC_IP = '1.1.1.1'


class TestIngressResourceFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestIngressResourceFactory, self).setUp()
        self.cloudformation = MagicMock()
        self.clients = MagicMock(speck=ClientCache)
        self.clients.cloudformation.return_value = self.cloudformation
        self.ingress = IngressResourceFactory(self.clients)
        for az_index, az in enumerate(self.other_orbit_region.azs.values()):
            az.nat_eip = '{0}.{0}.{0}.{0}'.format(az_index)
        self._multi_region()

    def test_ingress_resources_ip_block(self):
        resource = self._only(self._http_ingress(PUBLIC_IP_BLOCK))
        self.assertEquals(PUBLIC_IP_BLOCK, resource['Properties']['CidrIp'])

    def test_ingress_resources_region(self):
        resource = self._only(self._http_ingress(ORBIT_REGION))
        self.assertEquals(PRIVATE_IP_BLOCK, resource['Properties']['CidrIp'])

    def test_ingress_resources_other_region_nat(self):
        self.ingress._app_eips = MagicMock(return_value=[])
        resources = self._http_ingress(OTHER_REGION)
        # 1 per Nat EIP:
        self.assertEquals(3, len(resources))
        for resource in resources.values():
            self.assertIn('CidrIp', resource['Properties'])

    def test_ingress_resources_other_region(self):
        self.ingress._app_eips = MagicMock(return_value=['1.1.1.1', '2.2.2.2'])
        resources = self._http_ingress(OTHER_REGION)
        # 1 per App EIP:
        self.assertEquals(2, len(resources))
        for resource in resources.values():
            self.assertIn('CidrIp', resource['Properties'])

    def test_ingress_resource_app(self):
        self.ingress._app_sg = MagicMock(return_value=SECURITY_GROUP)
        resource = self._only(self._http_ingress('foo'))
        self.assertNotIn('CidrIp', resource['Properties'])
        self.assertEquals(SECURITY_GROUP,
                          resource['Properties']['SourceSecurityGroupId'])

    def test_ingress_resource_app_not_found(self):
        self.ingress._app_sg = MagicMock(return_value=None)
        resources = self._http_ingress('foo')
        self.assertEquals(0, len(resources))

    def test_app_sg(self):
        self.cloudformation.describe_stack_resource.return_value = {
            'StackResourceDetail': {
                'PhysicalResourceId': SECURITY_GROUP
            }
        }
        sg = self.ingress._app_sg(self.orbit, ORBIT_REGION, 'test-app')
        self.assertEquals(SECURITY_GROUP, sg)

    def test_app_sg_not_found(self):
        self._describe_stack_resource_error('Stack does not exist')
        sg = self.ingress._app_sg(self.orbit, ORBIT_REGION, 'test-app')
        self.assertIsNone(sg)

    def test_app_sg_error(self):
        self._describe_stack_resource_error('Kaboom')
        self.assertRaises(ClientError, self.ingress._app_sg, self.orbit,
                          ORBIT_REGION, 'test-app')

    def test_app_eips(self):
        resource_list = [{
            'StackResourceSummaries': [{
                'LogicalResourceId': 'ElasticIp01',
                'PhysicalResourceId': ELASTIC_IP
            }]
        }]
        pages = MagicMock()
        pages.paginate = MagicMock(return_value=resource_list)
        self.cloudformation.get_paginator = MagicMock(return_value=pages)

        eips = self.ingress._app_eips(self.orbit_region, 'test-app')
        self.assertIn(ELASTIC_IP, eips)

    def test_app_eips_error(self):
        self.cloudformation.get_paginator.side_effect = ClientError({
            'Error': {
                'Message': 'Kaboom'
            }
        }, 'GetPaginator')
        self.assertRaises(ClientError, self.ingress._app_eips,
                          self.orbit_region, 'test-app')

    def test_app_eips_cloudformation_stack_does_not_exist(self):
        self.cloudformation.get_paginator.side_effect = ClientError({
            'Error': {
                'Message': 'CloudFormation stack does not exist'
            }
        }, 'GetPaginator')
        eips = self.ingress._app_eips(self.orbit_region, 'test-app')
        self.assertEquals(0, len(eips))

    def test_ingress_resources_availability_internet(self):
        self._availability(PUBLIC_IP_BLOCK, 'internet-facing', True)
        self._availability(PRIVATE_IP_BLOCK, 'internet-facing', True)

    def test_ingress_resources_availability_multiregion(self):
        self._availability(PUBLIC_IP_BLOCK, 'multi-region', False)
        self._availability(PRIVATE_IP_BLOCK, 'multi-region', True)

    def test_ingress_resources_availability_private(self):
        self._availability(PUBLIC_IP_BLOCK, 'private', False)
        self._availability(PRIVATE_IP_BLOCK, 'private', True)

    def test_is_rfc1918(self):
        self.assertTrue(self._rfc1918(PRIVATE_IP_BLOCK))
        self.assertTrue(self._rfc1918('10.0.0.0/8'))
        self.assertTrue(self._rfc1918('010.010.010.010/8'))
        self.assertTrue(self._rfc1918('172.16.0.0/12'))
        self.assertTrue(self._rfc1918('192.168.0.0/16'))

        self.assertFalse(self._rfc1918(PUBLIC_IP_BLOCK))
        self.assertFalse(self._rfc1918('172.15.0.0/24'))
        self.assertFalse(self._rfc1918('192.167.0.0/24'))

    def _http_ingress(self, *args, **kwargs):
        return self.ingress.ingress_resources(self.app_region, 80, args,
                                              **kwargs)

    def _only(self, resources):
        self.assertEquals(1, len(resources))
        return six.next(six.itervalues(resources))

    def _describe_stack_resource_error(self, message):
        self.cloudformation.describe_stack_resource.side_effect = ClientError({
            'Error': {
                'Message': message
            }
        }, 'CreateSubnet')

    def _availability(self, param, availability, allowed):
        resources = self._http_ingress(param, availability=availability)
        self.assertEquals(allowed and 1 or 0, len(resources))

    def _rfc1918(self, ip_block):
        ip_match = IP_BLOCK.match(ip_block)
        return self.ingress._is_rfc1918(ip_match)
