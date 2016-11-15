import logging

from spacel.model.aws import VALID_REGIONS

logger = logging.getLogger('spacel.model.orbit')

GDH_PARENT = 'parent_stack'
GDH_DEPLOY = 'deploy_stack'


class Orbit(object):
    def __init__(self, name=None, regions=()):
        self.name = name
        self.regions = {}
        for region in regions:
            if region in VALID_REGIONS:
                self.regions[region] = OrbitRegion()
                continue

            logger.warn('Orbit "%s" has invalid region "%s". Valid regions: %s',
                        name, region, ', '.join(VALID_REGIONS))

    @property
    def valid(self):
        if not self.name or not self.regions:
            return False

        for orbit_region in self.regions.values():
            if not orbit_region.valid:
                return False

        return True


class OrbitRegion(object):
    def __init__(self,
                 bastion_instance_count=1,
                 bastion_instance_type='t2.nano',
                 bastion_sources=['0.0.0.0/0'],
                 deploy_stack=None,
                 domain=None,
                 nat_enabled=True,
                 nat_per_az=False,
                 parent_stack=None,
                 private_network='192.168',
                 provider='spacel'
                 ):
        self.bastion_instance_count = bastion_instance_count
        self.bastion_instance_type = bastion_instance_type
        self.bastion_sources = bastion_sources
        self.deploy_stack = deploy_stack
        self.domain = domain
        self.nat_enabled = nat_enabled
        self.nat_per_az = nat_per_az
        self.parent_stack = parent_stack
        self.private_network = private_network
        self.provider = provider

        # Queried from EC2:
        self._azs = []

        # Output from VPC:
        self._vpc_id = None

        # # Output from VPC:
        # self._vpc_ids = {}
        # self._nat_eips = defaultdict(dict)
        # self._public_instance_subnets = defaultdict(dict)
        # self._public_elb_subnets = defaultdict(dict)
        # self._private_instance_subnets = defaultdict(dict)
        # self._private_elb_subnets = defaultdict(dict)
        # self._private_cache_subnet_groups = {}
        # self._private_rds_subnet_groups = {}
        # self._public_rds_subnet_groups = {}
        # self._spot_fleet_role = {}
        #
        # # Output from Bastion:
        # self._bastion_eips = defaultdict(dict)
        # self._bastion_sgs = {}

    @property
    def valid(self):
        if self.provider == 'spacel':
            return True
        elif self.provider == 'gdh':
            return True
        return False
