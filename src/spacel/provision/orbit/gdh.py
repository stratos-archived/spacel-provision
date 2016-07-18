from botocore.exceptions import ClientError
import logging
from spacel.provision.cloudformation import (BaseCloudFormationFactory,
                                             key_sorted)

logger = logging.getLogger('spacel')


class GitDeployHooksOrbitFactory(BaseCloudFormationFactory):
    """
    Queries existing orbital VPCs built by git-deploy.
    """

    def __init__(self, clients, parent_stack):
        super(GitDeployHooksOrbitFactory, self).__init__(clients)
        self._stack_name = parent_stack

    def get_orbit(self, orbit):
        for region in orbit.regions:
            cf = self._clients.cloudformation(region)

            # Check for parent in region:
            name = orbit.name
            logger.debug('Querying %s in %s...', name, region)
            try:
                parent_resource = cf.describe_stack_resource(
                    StackName=self._stack_name, LogicalResourceId=name)
            except ClientError as e:
                e_message = e.response['Error'].get('Message', '')
                if 'does not exist' in e_message:
                    logger.warn('Orbit %s not found in %s.', name, region)
                    continue
                raise e

            # Parent found, query child:
            child_resource_id = (parent_resource
                                 ['StackResourceDetail']
                                 ['PhysicalResourceId'])
            logger.debug('Querying %s for outputs...', child_resource_id)
            child_stack = self._describe_stack(cf, child_resource_id)
            outputs = child_stack.get('Outputs', ())

            self._orbit_from_child(orbit, region, name, outputs)

    @staticmethod
    def _orbit_from_child(orbit, region, name, cf_outputs):
        # Map outputs onto orbit model:
        private_subnets = {}
        public_subnets = {}
        for output in cf_outputs:
            key = output['OutputKey']
            value = output['OutputValue']
            if key.startswith('PrivateSubnet'):
                private_subnets[key[-2:]] = value
            elif key.startswith('PublicSubnet'):
                public_subnets[key[-2:]] = value
            elif key.startswith('NATElasticIP'):
                orbit._nat_eips[region][key[-2:]] = value
            elif key.startswith('EnvironmentVpcId'):
                orbit._vpc_ids[region] = value
            elif key.startswith('PublicRouteTable'):
                continue
            elif key.startswith('PrivateRouteTable'):
                continue
            elif key == 'CIDR':
                continue
            else:
                logger.warn('Unrecognized output key: %s', key)
        public_subnets = key_sorted(public_subnets)
        private_subnets = key_sorted(private_subnets)
        orbit._public_instance_subnets[region] = public_subnets
        orbit._public_elb_subnets[region] = public_subnets
        orbit._private_instance_subnets[region] = private_subnets
        orbit._private_elb_subnets[region] = private_subnets
        logger.debug('Updated %s in %s.', name, region)
