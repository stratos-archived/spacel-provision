from botocore.exceptions import ClientError
from mock import MagicMock

from spacel.aws import ClientCache
from spacel.provision.changesets import ChangeSetEstimator
from spacel.provision.orbit.gdh import GitDeployHooksOrbitFactory
from spacel.provision.s3 import TemplateUploader
from test import BaseSpaceAppTest, ORBIT_REGION
from test.provision.orbit import (NAME, VPC_ID, IP_ADDRESS, cf_outputs,
                                  cf_parameters)

PARENT_NAME = 'daddy'
DEPLOY_NAME = 'deploy'
STACK_ID = 'arn:cloudformation:123456'
ROLE_SPOT_FLEET = 'arn:iam:role:123456'


class TestGitDeployHooksOrbitFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestGitDeployHooksOrbitFactory, self).setUp()
        self.clients = MagicMock(spec=ClientCache)
        self.cloudformation = MagicMock()
        self.cloudformation.describe_stack_resource.return_value = {
            'StackResourceDetail': {
                'PhysicalResourceId': STACK_ID
            }
        }
        self.clients.cloudformation.return_value = self.cloudformation
        self.orbit.regions[ORBIT_REGION].parent_stack = PARENT_NAME
        self.orbit.regions[ORBIT_REGION].deploy_stack = DEPLOY_NAME

        self.change_sets = MagicMock(spec=ChangeSetEstimator)
        self.templates = MagicMock(spec=TemplateUploader)
        self.orbit_factory = GitDeployHooksOrbitFactory(self.clients,
                                                        self.change_sets,
                                                        self.templates)
        self.orbit_factory._describe_stack = MagicMock()

    def test_get_orbit(self):
        self.orbit_factory._orbit_from_child = MagicMock()
        self.orbit_factory._describe_stack.return_value = {
            'Outputs': [{
                'OutputKey': 'SecurityGroup',
                'OutputValue': 'sg-000001'
            }]
        }

        self.orbit_factory.orbit(self.orbit)

        self.cloudformation.describe_stack_resource.assert_called_once()
        self.orbit_factory._orbit_from_child.assert_called_once()
        self.assertEqual(self.orbit_region.bastion_sg, 'sg-000001')

    def test_get_orbit_not_found(self):
        self._describe_stack_resource_error('Stack does not exist')
        self.orbit_factory._orbit_from_child = MagicMock()

        self.orbit_factory.orbit(self.orbit)

        self.orbit_factory._orbit_from_child.assert_not_called()

    def test_get_orbit_error(self):
        self._describe_stack_resource_error('kaboom')

        self.assertRaises(ClientError, self.orbit_factory.orbit, self.orbit)

    def _describe_stack_resource_error(self, message):
        self.cloudformation.describe_stack_resource.side_effect = ClientError({
            'Error': {
                'Message': message
            }
        }, 'CreateSubnet')

    def test_orbit_from_child(self):
        params = {
            'Az1': 'us-west-2a',
            'Az2': 'us-west-2b',
            'Az3': 'us-west-2c',
        }
        outputs = {
            'PrivateSubnet01': 'subnet-000001',
            'PrivateSubnet02': 'subnet-000002',
            'PublicSubnet01': 'subnet-000101',
            'PublicRouteTable': 'rtb-000001',
            'PrivateRouteTable': 'rtb-000002',
            'NATElasticIP01': IP_ADDRESS,
            'EnvironmentVpcId': VPC_ID,
            'PrivateCacheSubnetGroup': 'subnet-000000',
            'PublicRdsSubnetGroup': 'subnet-000000',
            'PrivateRdsSubnetGroup': 'subnet-000000',
            'RoleSpotFleet': ROLE_SPOT_FLEET,
            'CIDR': '%s/32' % IP_ADDRESS,
            'Unknown': 'AndThatsOk'
        }

        self.orbit_factory._orbit_from_child(self.orbit_region, NAME,
                                             cf_parameters(params),
                                             cf_outputs(outputs))
        self.assertEquals(['us-west-2a', 'us-west-2b', 'us-west-2c'],
                          self.orbit_region.az_keys)

        self.assertEquals('subnet-000001', (self.orbit_region.azs['us-west-2a']
                                            .private_elb_subnet))
        self.assertEquals('subnet-000002', (self.orbit_region.azs['us-west-2b']
                                            .private_elb_subnet))
        self.assertEquals('subnet-000001', (self.orbit_region.azs['us-west-2a']
                                            .private_instance_subnet))
        self.assertEquals('subnet-000002', (self.orbit_region.azs['us-west-2b']
                                            .private_instance_subnet))

        self.assertEquals('subnet-000101', (self.orbit_region.azs['us-west-2a']
                                            .public_elb_subnet))

        self.assertEquals(VPC_ID, self.orbit_region.vpc_id)
        self.assertEquals(ROLE_SPOT_FLEET,
                          self.orbit_region.spot_fleet_role)
        self.assertEquals('subnet-000000',
                          self.orbit_region.public_rds_subnet_group)
        self.assertEquals('subnet-000000',
                          self.orbit_region.private_rds_subnet_group)
        self.assertEquals('subnet-000000',
                          self.orbit_region.private_cache_subnet_group)
