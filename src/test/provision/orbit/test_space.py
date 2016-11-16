from botocore.exceptions import ClientError
from mock import MagicMock

from spacel.aws import ClientCache
from spacel.provision.changesets import ChangeSetEstimator
from spacel.provision.orbit.space import SpaceElevatorOrbitFactory
from spacel.provision.s3 import TemplateUploader
from spacel.provision.template import (VpcTemplate, BastionTemplate,
                                       TablesTemplate)
from test import BaseSpaceAppTest, ORBIT_REGION
from test.provision.orbit import (VPC_ID, IP_ADDRESS, cf_outputs)

SECURITY_GROUP_ID = 'sg-123456'
SPOTFLEET_ROLE_ARN = 'arn:aws:iam::1234567890:role/spot-fleet-role'


class TestSpaceElevatorOrbitFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestSpaceElevatorOrbitFactory, self).setUp()
        self.vpc_template = MagicMock(spec=VpcTemplate)
        self.vpc_template.vpc.return_value = {'Spacel': 'Rules'}
        self.bastion_template = MagicMock(spec=BastionTemplate)
        self.bastion_template.bastion.return_value = {'Spacel': 'Rules'}
        self.tables_template = MagicMock(spec=TablesTemplate)
        self.tables_template.tables.return_value = {'Spacel': 'Rules'}
        self.clients = MagicMock(spec=ClientCache)
        self.change_sets = MagicMock(spec=ChangeSetEstimator)
        self.templates = MagicMock(spec=TemplateUploader)
        self.ec2 = MagicMock()
        self.clients.ec2.return_value = self.ec2

        self.orbit_factory = SpaceElevatorOrbitFactory(self.clients,
                                                       self.change_sets,
                                                       self.templates,
                                                       self.vpc_template,
                                                       self.bastion_template,
                                                       self.tables_template)

    def test_get_orbit(self):
        self.orbit_region.bastion_eips.append(IP_ADDRESS)

        self.orbit_factory._azs = MagicMock()
        self.orbit_factory._orbit_stack = MagicMock()

        self.orbit_factory.orbit(self.orbit, self.orbit.regions)

        self.orbit_factory._azs.assert_called_once()
        self.assertEquals(3, self.orbit_factory._orbit_stack.call_count)

    def test_orbit_stack_vpc_noop(self):
        self.orbit_factory._stack = MagicMock(return_value=None)
        self.orbit_factory._wait_for_updates = MagicMock()
        self.orbit_factory._orbit_from_vpc = MagicMock()
        self.orbit_factory._orbit_from_bastion = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions, 'vpc')

        self.vpc_template.vpc.assert_called_once_with(self.orbit_region)
        self.orbit_factory._wait_for_updates.assert_called_once()
        self.orbit_factory._orbit_from_vpc.assert_called_once()
        self.orbit_factory._orbit_from_bastion.assert_not_called()

    def test_orbit_stack_bastion_update(self):
        self.orbit_factory._stack = MagicMock(return_value='update')
        self.orbit_factory._wait_for_updates = MagicMock()
        self.orbit_factory._orbit_from_vpc = MagicMock()
        self.orbit_factory._orbit_from_bastion = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions,
                                        'bastion')

        self.vpc_template.vpc.assert_not_called()
        self.bastion_template.bastion.assert_called_once_with(
            self.orbit_region)
        self.orbit_factory._wait_for_updates.assert_called_once()
        self.orbit_factory._orbit_from_vpc.assert_not_called()
        self.orbit_factory._orbit_from_bastion.assert_called_once()

    def test_orbit_stack_tables_noop(self):
        self.vpc_template.vpc.return_value = {}
        self.bastion_template.bastion.return_value = {}
        self.tables_template.tables.return_value = {}
        self.orbit_factory._stack = MagicMock(return_value=None)
        self.orbit_factory._wait_for_updates = MagicMock()
        self.orbit_factory._orbit_from_vpc = MagicMock()
        self.orbit_factory._orbit_from_bastion = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions,
                                        'tables')

        self.orbit_factory._wait_for_updates.assert_not_called()
        self.orbit_factory._orbit_from_vpc.assert_not_called()
        self.orbit_factory._orbit_from_bastion.assert_not_called()

    def test_orbit_stack_noop(self):
        self.orbit_factory._stack = MagicMock(return_value=None)
        self.orbit_factory._wait_for_updates = MagicMock()
        self.orbit_factory._orbit_from_vpc = MagicMock()
        self.orbit_factory._orbit_from_bastion = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions,
                                        'tables')

        self.tables_template.tables.assert_called_once_with(self.orbit)
        self.orbit_factory._orbit_from_vpc.assert_not_called()
        self.orbit_factory._orbit_from_bastion.assert_not_called()

    def test_orbit_stack_unknown(self):
        self.orbit_factory._stack = MagicMock()
        self.orbit_factory._wait_for_updates = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions,
                                        'kaboom')

        self.orbit_factory._stack.assert_not_called()
        self.orbit_factory._wait_for_updates.assert_not_called()

    def test_azs(self):
        self._create_subnet_error(
            'us-west-2zzz is invalid. Subnets can currently only be created in '
            'the following availability zones: us-west-2a, us-west-2b')

        self.orbit_factory._azs(self.orbit, self.orbit.regions)

        self.clients.ec2.assert_called_once_with(ORBIT_REGION)
        self.ec2.create_subnet.assert_called_once()
        self.assertEquals(['us-west-2a', 'us-west-2b'],
                          self.orbit_region.az_keys)

    def test_azs_skip(self):
        self.orbit_region.az_keys = []
        self._create_subnet_error(
            'us-west-2zzz is invalid. Subnets can currently only be created in '
            'the following availability zones: us-west-2a, us-west-2b')

        self.orbit_factory._azs(self.orbit, ['eu-west-1'])

        self.clients.ec2.assert_not_called()
        self.assertEquals([], self.orbit_region.az_keys)

    def test_azs_error(self):
        self._create_subnet_error('Kaboom')
        self.assertRaises(ClientError, self.orbit_factory._azs, self.orbit,
                          self.orbit.regions)

    def _create_subnet_error(self, message):
        self.ec2.create_subnet.side_effect = ClientError({
            'Error': {
                'Message': message
            }
        }, 'CreateSubnet')

    def test_orbit_from_vpc(self):
        outputs = {
            'PrivateInstanceSubnet01': 'subnet-000001',
            'PrivateInstanceSubnet02': 'subnet-000002',
            'PrivateElbSubnet01': 'subnet-000011',
            'PrivateElbSubnet02': 'subnet-000012',
            'PublicInstanceSubnet01': 'subnet-000101',
            'PublicElbSubnet01': 'subnet-000111',
            'PublicNatSubnet01': 'subnet-000121',
            'NatEip01': IP_ADDRESS,
            'VpcId': VPC_ID,
            'PublicRdsSubnetGroup': 'public-rds',
            'PrivateRdsSubnetGroup': 'private-rds',
            'PrivateCacheSubnetGroup': 'private-rds',
            'PrivateCacheSubnet01': 'subnet-666666',
            'PrivateRdsSubnet01': 'subnet-777777',
            'RoleSpotFleet': SPOTFLEET_ROLE_ARN,
            'Unknown': 'AndThatsOk'

        }

        self.orbit_factory._orbit_from_vpc(self.orbit_region,
                                           cf_outputs(outputs))

        self.assertEquals('subnet-000011', (self.orbit_region.azs['us-west-2a']
                                            .private_elb_subnet))
        self.assertEquals('subnet-000012', (self.orbit_region.azs['us-west-2b']
                                            .private_elb_subnet))
        self.assertEquals('subnet-000001', (self.orbit_region.azs['us-west-2a']
                                            .private_instance_subnet))
        self.assertEquals('subnet-000002', (self.orbit_region.azs['us-west-2b']
                                            .private_instance_subnet))

        self.assertEquals('subnet-000101', (self.orbit_region.azs['us-west-2a']
                                            .public_instance_subnet))
        self.assertEquals('subnet-000111', (self.orbit_region.azs['us-west-2a']
                                            .public_elb_subnet))
        self.assertEquals(VPC_ID, self.orbit_region.vpc_id)
        self.assertEquals(SPOTFLEET_ROLE_ARN, self.orbit_region.spot_fleet_role)
        self.assertEquals('private-rds',
                          self.orbit_region.private_rds_subnet_group)

    def test_orbit_from_bastion(self):
        outputs = {
            'ElasticIp01': IP_ADDRESS,
            'ElasticIp02': '127.0.0.2',
            'BastionSecurityGroup': SECURITY_GROUP_ID,
            'Unknown': 'AndThatsOk'
        }

        self.orbit_factory._orbit_from_bastion(self.orbit_region,
                                               cf_outputs(outputs))

        self.assertEquals(SECURITY_GROUP_ID, self.orbit_region.bastion_sg)
        self.assertEquals({IP_ADDRESS, '127.0.0.2'},
                          set(self.orbit_region.bastion_eips))

    def test_delete_orbit(self):
        self.orbit_factory._delete_stack = MagicMock(return_value=None)

        self.orbit_factory.delete_orbit(self.orbit)

        self.assertEquals(3, self.orbit_factory._delete_stack.call_count)
