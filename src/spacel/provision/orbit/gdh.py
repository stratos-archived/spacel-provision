import logging

from botocore.exceptions import ClientError

from spacel.provision.cloudformation import (BaseCloudFormationFactory)

logger = logging.getLogger('spacel.provision.orbit.gdh')


class GitDeployHooksOrbitFactory(BaseCloudFormationFactory):
    """
    Queries existing orbital VPCs built by git-deploy.
    """

    def get_orbit(self, orbit, regions=None):
        regions = regions or orbit.regions
        for region in regions:
            orbit_region = orbit.regions[region]
            cf = self._clients.cloudformation(region)

            # Check for parent in region:
            name = orbit.name
            logger.debug('Querying %s in %s...', name, region)
            try:
                parent_resource = cf.describe_stack_resource(
                    StackName=orbit_region.parent_stack, LogicalResourceId=name)
            except ClientError as e:
                e_message = e.response['Error'].get('Message', '')
                if 'does not exist' in e_message:
                    logger.warning('Orbit %s not found in %s.', name, region)
                    continue
                raise e

            # Parent found, query child:
            child_resource_id = (parent_resource
                                 ['StackResourceDetail']
                                 ['PhysicalResourceId'])
            logger.debug('Querying %s for outputs...', child_resource_id)
            child_stack = self._describe_stack(cf, child_resource_id)
            parameters = child_stack.get('Parameters', ())
            outputs = child_stack.get('Outputs', ())

            self._orbit_from_child(orbit, region, name, parameters, outputs)

            deploy_stack = self._describe_stack(cf, orbit_region.deploy_stack)
            outputs = deploy_stack.get('Outputs', ())
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                if key == 'SecurityGroup':
                    orbit_region.bastion_sg = value

    @staticmethod
    def _orbit_from_child(orbit_region, name, cf_parameters, cf_outputs):
        # Map parameters onto orbit model:
        azs = []
        for parameter in cf_parameters:
            key = parameter['ParameterKey']
            value = parameter['ParameterValue']
            if key.startswith('Az'):
                azs.append(value)
        orbit_region.az_keys = sorted(azs)

        # Index AZs of the region by label: {01:us-east-1a, 02:us-east-1b} etc.
        az_map = {'%02d' % (i + 1): orbit_region.azs[az_key]
                  for i, az_key in enumerate(orbit_region.az_keys)}

        # Map outputs onto orbit model:
        for output in cf_outputs:
            key = output['OutputKey']
            value = output['OutputValue']
            orbit_region_az = az_map.get(key[-2:])
            if orbit_region_az:
                if key.startswith('PrivateSubnet'):
                    orbit_region_az.private_instance_subnet = value
                    orbit_region_az.private_elb_subnet = value
                    continue
                elif key.startswith('PublicSubnet'):
                    orbit_region_az.public_instance_subnet = value
                    orbit_region_az.public_elb_subnet = value
                    continue
                elif key.startswith('NATElasticIP'):
                    orbit_region.nat_eips.append(value)
            else:
                if key.startswith('EnvironmentVpcId'):
                    orbit_region.vpc_id = value
                    continue
                elif key.startswith('PrivateCacheSubnetGroup'):
                    orbit_region.private_cache_subnet_group = value
                    continue
                elif key.startswith('PublicRdsSubnetGroup'):
                    orbit_region.public_rds_subnet_group = value
                    continue
                elif key.startswith('PrivateRdsSubnetGroup'):
                    orbit_region.private_rds_subnet_group = value
                    continue
                elif key.startswith('RoleSpotFleet'):
                    orbit_region.spot_fleet_role = value
                    continue
                elif (key.startswith('PublicRouteTable')
                      or key.startswith('PrivateRouteTable')
                      or key == 'CIDR'):
                    continue
            logger.warning('Unrecognized output key: %s', key)
        logger.debug('Updated %s in %s.', name, orbit_region.region)
