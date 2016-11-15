import logging

from botocore.exceptions import ClientError

from spacel.provision.cloudformation import (BaseCloudFormationFactory)

logger = logging.getLogger('spacel.provision.orbit.spacel')


class SpaceElevatorOrbitFactory(BaseCloudFormationFactory):
    """
    Builds orbital VPCs based on Space Elevator templates.
    """

    def __init__(self, clients, change_sets, uploader, vpc, bastion, tables):
        super(SpaceElevatorOrbitFactory, self).__init__(clients, change_sets,
                                                        uploader)
        self._vpc = vpc
        self._bastion = bastion
        self._tables = tables

    def get_orbit(self, orbit, regions=None):
        regions = regions or orbit.regions.keys()
        self._azs(orbit, regions)
        self._orbit_stack(orbit, regions, 'vpc')
        self._orbit_stack(orbit, regions, 'tables')
        self._orbit_stack(orbit, regions, 'bastion')

    def _orbit_stack(self, orbit, regions, stack_suffix):
        stack_name = '%s-%s' % (orbit.name, stack_suffix)

        updates = {}
        for region in regions:
            logger.debug('Provisioning %s in %s.', stack_name, region)
            orbit_region = orbit.regions[region]
            if stack_suffix == 'vpc':
                template = self._vpc.vpc(orbit_region)
            elif stack_suffix == 'bastion':
                template = self._bastion.bastion(orbit_region)
            elif stack_suffix == 'tables':
                template = self._tables.tables(orbit)
            else:
                logger.warning('Unknown orbit template: %s', stack_suffix)
                return

            if not template:
                return

            updates[region] = self._stack(stack_name, region, template)

        logger.debug('Requested %s in %s, waiting for provisioning...',
                     stack_name, regions)
        self._wait_for_updates(stack_name, updates)
        logger.debug('Provisioned %s in %s.', stack_name, regions)

        # Refresh model from CF:
        for region in regions:
            cf = self._clients.cloudformation(region)
            cf_stack = self._describe_stack(cf, stack_name)
            cf_outputs = cf_stack.get('Outputs', {})
            orbit_region = orbit.regions[region]
            if stack_suffix == 'tables':
                continue
            elif stack_suffix == 'vpc':
                self._orbit_from_vpc(orbit_region, cf_outputs)
            elif stack_suffix == 'bastion':
                self._orbit_from_bastion(orbit_region, cf_outputs)
            else:  # pragma: no cover
                logger.warning('Unknown suffix: %s', stack_suffix)

    def _azs(self, orbit, regions):
        for region, orbit_region in orbit.regions.items():
            if regions and region not in regions:
                continue

            ec2 = self._clients.ec2(region)
            try:
                vpcs = ec2.describe_vpcs()
                vpc_id = vpcs['Vpcs'][0]['VpcId']
                invalid_az = region + '-zzz'
                ec2.create_subnet(VpcId=vpc_id, CidrBlock='172.31.192.0/20',
                                  AvailabilityZone=invalid_az)
            except ClientError as e:
                message = e.response['Error'].get('Message')
                if not message or 'Subnets can currently only be created in ' \
                                  'the following availability zones' not in message:
                    raise e
                message_split = message.split(region)
                # Invalid region echoed, every mention after that is an AZ:
                azs = sorted([region + s[0] for s in message_split[2:]])
                orbit_region.az_keys = azs

    @staticmethod
    def _orbit_from_vpc(orbit_region, cf_outputs):
        logger.debug('Updating %s in %s from VPC CloudFormation.',
                     orbit_region.orbit.name, orbit_region.region)

        # Index AZs of the region by label: {01:us-east-1a, 02:us-east-1b} etc.
        az_map = {'%02d' % (i + 1): orbit_region.azs[az_key]
                  for i, az_key in enumerate(orbit_region.az_keys)}

        for output in cf_outputs:
            key = output['OutputKey']
            value = output['OutputValue']

            # Keys ending in ## are per-AZ:
            orbit_region_az = az_map.get(key[-2:])
            if orbit_region_az:
                # Per-AZ outputs:
                if key.startswith('PrivateInstanceSubnet'):
                    orbit_region_az.private_instance_subnet = value
                    continue
                elif key.startswith('NatEip'):
                    orbit_region_az.nat_eip = value
                    continue
                elif key.startswith('PrivateElbSubnet'):
                    orbit_region_az.private_elb_subnet = value
                    continue
                elif key.startswith('PublicInstanceSubnet'):
                    orbit_region_az.public_instance_subnet = value
                    continue
                elif key.startswith('PublicElbSubnet'):
                    orbit_region_az.public_elb_subnet = value
                    continue
                elif ('PublicNatSubnet' in key
                      or 'CacheSubnet' in key
                      or 'RdsSubnet' in key):
                    continue
            else:
                # Per-region outputs:
                if key.startswith('VpcId'):
                    orbit_region.vpc_id = value
                    continue
                elif key == 'PublicRdsSubnetGroup':
                    orbit_region.public_rds_subnet_group = value
                    continue
                elif key == 'PrivateRdsSubnetGroup':
                    orbit_region.private_rds_subnet_group = value
                    continue
                elif key == 'PrivateCacheSubnetGroup':
                    orbit_region.private_cache_subnet_group = value
                    continue
                elif key == 'RoleSpotFleet':
                    orbit_region.spot_fleet_role = value
                    continue
            logger.warning('Unrecognized output key: %s', key)

    @staticmethod
    def _orbit_from_bastion(orbit_region, cf_outputs):
        logger.debug('Updating %s from Bastion CloudFormation.',
                     orbit_region.orbit.name)
        for output in cf_outputs:
            key = output['OutputKey']
            value = output['OutputValue']
            if key.startswith('ElasticIp'):
                orbit_region.bastion_eips.append(value)
            elif key.startswith('BastionSecurityGroup'):
                orbit_region.bastion_sg = value
            else:
                logger.warning('Unrecognized output key: %s', key)

    def delete_orbit(self, orbit, regions=None):
        regions = regions or orbit.regions

        bastion_name = '%s-bastion' % orbit.name
        tables_name = '%s-tables' % orbit.name
        vpc_name = '%s-vpc' % orbit.name

        # Bastions and tables can be deleted concurrently:
        bastion_updates = {}
        tables_updates = {}
        for region in regions:
            bastion_updates[region] = self._delete_stack(bastion_name, region)
            tables_updates[region] = self._delete_stack(tables_name, region)
        self._wait_for_updates(bastion_name, bastion_updates)

        # VPC can be deleted after bastion completes:
        vpc_updates = {}
        for region in regions:
            vpc_updates[region] = self._delete_stack(vpc_name, region)
        self._wait_for_updates(vpc_name, vpc_updates)

        # Tables should be gone by now, but let's 100%:
        self._wait_for_updates(tables_name, tables_updates)
