from botocore.exceptions import ClientError
from mock import MagicMock
import unittest

from spacel.aws import ClientCache
from spacel.model import Orbit
from spacel.provision.templates import TemplateCache
from spacel.provision.orbit.space import SpaceElevatorOrbitFactory

from test.provision.orbit import (NAME, REGION, VPC_ID, IP_ADDRESS, cf_outputs)

SECURITY_GROUP_ID = 'sg-123456'


class TestSpaceElevatorOrbitFactory(unittest.TestCase):
    def setUp(self):
        self.templates = MagicMock(spec=TemplateCache)
        self.templates.vpc.return_value = {}
        self.templates.bastion.return_value = {}
        self.templates.tables.return_value = {}
        self.clients = MagicMock(spec=ClientCache)
        self.ec2 = MagicMock()
        self.clients.ec2.return_value = self.ec2
        self.orbit = Orbit(NAME, {
            'regions': (REGION,)
        })
        self.orbit_factory = SpaceElevatorOrbitFactory(self.clients,
                                                       self.templates)

    def test_get_orbit(self):
        self.orbit._bastion_eips[REGION] = {'01': IP_ADDRESS}

        self.orbit_factory._azs = MagicMock()
        self.orbit_factory._orbit_stack = MagicMock()

        self.orbit_factory.get_orbit(self.orbit, self.orbit.regions)

        self.orbit_factory._azs.assert_called_once()
        self.assertEquals(3, self.orbit_factory._orbit_stack.call_count)

    def test_orbit_stack_vpc_noop(self):
        self.orbit_factory._stack = MagicMock(return_value=None)
        self.orbit_factory._wait_for_updates = MagicMock()
        self.orbit_factory._orbit_from_vpc = MagicMock()
        self.orbit_factory._orbit_from_bastion = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions, 'vpc')

        self.templates.vpc.assert_called_once_with(self.orbit, REGION)
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

        self.templates.vpc.assert_not_called()
        self.templates.bastion.assert_called_once_with(self.orbit, REGION)
        self.orbit_factory._wait_for_updates.assert_called_once()
        self.orbit_factory._orbit_from_vpc.assert_not_called()
        self.orbit_factory._orbit_from_bastion.assert_called_once()

    def test_orbit_stack_tables_noop(self):
        self.orbit_factory._stack = MagicMock(return_value=None)
        self.orbit_factory._wait_for_updates = MagicMock()
        self.orbit_factory._orbit_from_vpc = MagicMock()
        self.orbit_factory._orbit_from_bastion = MagicMock()

        self.orbit_factory._orbit_stack(self.orbit, self.orbit.regions,
                                        'tables')

        self.templates.tables.assert_called_once_with(self.orbit)
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
            'us-east-1zzz is invalid. Subnets can currently only be created in '
            'the following availability zones: us-east-1a, us-east-1b')

        self.orbit_factory._azs(self.orbit, self.orbit.regions)

        self.clients.ec2.assert_called_once_with(REGION)
        self.ec2.create_subnet.assert_called_once()
        self.assertEquals(['us-east-1a', 'us-east-1b'], self.orbit.azs(REGION))

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
            'PrivateElbSubnet01': 'subnet-000012',
            'PrivateElbSubnet02': 'subnet-000011',
            'PublicInstanceSubnet': 'subnet-000101',
            'PublicElbSubnet': 'subnet-000111',
            'PublicNatSubnet': 'subnet-000121',
            'NatEip': IP_ADDRESS,
            'VpcId': VPC_ID,
            'Unknown': 'AndThatsOk'
        }

        self.orbit_factory._orbit_from_vpc(self.orbit, REGION,
                                           cf_outputs(outputs))

        self.assertEquals(['subnet-000001', 'subnet-000002'],
                          self.orbit.private_instance_subnets(REGION))
        self.assertEquals(['subnet-000012', 'subnet-000011'],
                          self.orbit.private_elb_subnets(REGION))
        self.assertEquals(['subnet-000101'],
                          self.orbit.public_instance_subnets(REGION))
        self.assertEquals(['subnet-000111'],
                          self.orbit.public_elb_subnets(REGION))
        self.assertEquals(VPC_ID, self.orbit.vpc_id(REGION))

    def test_orbit_from_bastion(self):
        outputs = {
            'ElasticIp01': IP_ADDRESS,
            'ElasticIp02': '127.0.0.2',
            'BastionSecurityGroup': SECURITY_GROUP_ID,
            'Unknown': 'AndThatsOk'
        }

        self.orbit_factory._orbit_from_bastion(self.orbit, REGION,
                                               cf_outputs(outputs))

        self.assertEquals(SECURITY_GROUP_ID, self.orbit.bastion_sg(REGION))
        self.assertEquals({'01': IP_ADDRESS, '02': '127.0.0.2'},
                          self.orbit.bastion_eips(REGION))
