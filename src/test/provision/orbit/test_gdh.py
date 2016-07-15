from botocore.exceptions import ClientError
from mock import MagicMock
import unittest

from spacel.model import Orbit
from spacel.provision.provision import ClientCache
from spacel.provision.orbit.gdh import GitDeployHooksOrbitFactory
from test.provision.orbit import (NAME, REGION, VPC_ID, IP_ADDRESS, cf_outputs)

PARENT_NAME = 'daddy'
STACK_ID = 'arn:cloudformation:123456'


class TestGitDeployHooksOrbitFactory(unittest.TestCase):
    def setUp(self):
        self.clients = MagicMock(spec=ClientCache)
        self.cloudformation = MagicMock()
        self.cloudformation.describe_stack_resource.return_value = {
            'StackResourceDetail': {
                'PhysicalResourceId': STACK_ID
            }
        }
        self.clients.cloudformation.return_value = self.cloudformation
        self.orbit = Orbit(NAME, {
            'regions': (REGION,)
        })

        self.orbit_factory = GitDeployHooksOrbitFactory(self.clients,
                                                        PARENT_NAME)
        self.orbit_factory._describe_stack = MagicMock()

    def test_get_orbit(self):
        self.orbit_factory._orbit_from_child = MagicMock()

        self.orbit_factory.get_orbit(self.orbit)

        self.cloudformation.describe_stack_resource.assert_called_once()
        self.orbit_factory._orbit_from_child.assert_called_once()

    def test_get_orbit_not_found(self):
        self._describe_stack_resource_error('Stack does not exist')
        self.orbit_factory._orbit_from_child = MagicMock()

        self.orbit_factory.get_orbit(self.orbit)

        self.orbit_factory._orbit_from_child.assert_not_called()

    def test_get_orbit_error(self):
        self._describe_stack_resource_error('kaboom')

        self.assertRaises(ClientError, self.orbit_factory.get_orbit, self.orbit)

    def _describe_stack_resource_error(self, message):
        self.cloudformation.describe_stack_resource.side_effect = ClientError({
            'Error': {
                'Message': message
            }
        }, 'CreateSubnet')

    def test_orbit_from_child(self):
        outputs = {
            'PrivateSubnet01': 'subnet-000001',
            'PrivateSubnet02': 'subnet-000002',
            'PublicSubnet01': 'subnet-000101',
            'PublicRouteTable': 'rtb-000001',
            'PrivateRouteTable': 'rtb-000002',
            'NATElasticIP01': IP_ADDRESS,
            'EnvironmentVpcId': VPC_ID,
            'CIDR': '%s/32' % IP_ADDRESS,
            'Unknown': 'AndThatsOk'
        }

        self.orbit_factory._orbit_from_child(self.orbit, REGION, NAME,
                                             cf_outputs(outputs))

        self.assertEquals(['subnet-000001', 'subnet-000002'],
                          self.orbit.private_instance_subnets(REGION))
        self.assertEquals(['subnet-000001', 'subnet-000002'],
                          self.orbit.private_elb_subnets(REGION))
        self.assertEquals(['subnet-000101'],
                          self.orbit.public_instance_subnets(REGION))
        self.assertEquals(['subnet-000101'],
                          self.orbit.public_elb_subnets(REGION))
        self.assertEquals(VPC_ID, self.orbit.vpc_id(REGION))
