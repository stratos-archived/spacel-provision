import logging

from spacel.model.aws import VALID_REGIONS

logger = logging.getLogger('spacel.model.orbit')

GDH_PARENT = 'parent_stack'
GDH_DEPLOY = 'deploy_stack'


class Orbit(object):
    def __init__(self, name=None, regions=(), **kwargs):
        self.name = name
        self.regions = {}
        for region in regions:
            if region in VALID_REGIONS:
                self.regions[region] = OrbitRegion(self, region, **kwargs)
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
                 orbit,
                 region,
                 bastion_instance_count=1,
                 bastion_instance_type='t2.nano',
                 bastion_sources=('0.0.0.0/0',),
                 deploy_stack=None,
                 domain=None,
                 nat_enabled=True,
                 nat_per_az=False,
                 parent_stack=None,
                 private_network='192.168',
                 provider='spacel'):
        self.orbit = orbit
        self.region = region
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
        self._azs = {}

        # Output from VPC:
        self.vpc_id = None
        self.nat_eips = []
        self.private_cache_subnet_group = None
        self.private_rds_subnet_group = None
        self.public_rds_subnet_group = None
        self.spot_fleet_role = None

        self.bastion_eips = []
        self.bastion_sg = None

    @property
    def azs(self):
        return self._azs

    @property
    def az_keys(self):
        return sorted(self._azs.keys())

    @az_keys.setter
    def az_keys(self, value):
        self._azs = {az: OrbitRegionAz() for az in value}

    @property
    def private_elb_subnets(self):
        return [self._azs[az_key].private_elb_subnet
                for az_key in self.az_keys]

    @property
    def private_instance_subnets(self):
        return [self._azs[az_key].private_instance_subnet
                for az_key in self.az_keys]

    @property
    def public_elb_subnets(self):
        return [self._azs[az_key].public_elb_subnet
                for az_key in self.az_keys]

    @property
    def public_instance_subnets(self):
        return [self._azs[az_key].public_instance_subnet
                for az_key in self.az_keys]


    @property
    def valid(self):
        if self.provider == 'spacel':
            return True
        elif self.provider == 'gdh':
            return True
        return False


class OrbitRegionAz(object):
    def __init__(self,
                 private_elb_subnet=None,
                 private_instance_subnet=None,
                 public_elb_subnet=None,
                 public_instance_subnet=None
                 ):
        self.private_elb_subnet = private_elb_subnet
        self.private_instance_subnet = private_instance_subnet
        self.public_elb_subnet = public_elb_subnet
        self.public_instance_subnet = public_instance_subnet
