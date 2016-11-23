import logging

from spacel.model.aws import VALID_REGIONS, INSTANCE_TYPES

logger = logging.getLogger('spacel.model.orbit')

NAT_CONFIGURATIONS = {
    'disabled',  # No NAT, don't even try
    'enabled',  # Single NAT gateway for every AZ (default)
    'per-az'  # NAT gateway per AZ (suggested for production)
}


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
                 parent_stack=None,
                 nat='enabled',
                 private_network='192.168',
                 provider='spacel'):
        self.orbit = orbit
        self.region = region
        self.provider = provider

        # provider: spacel:
        self.bastion_instance_count = bastion_instance_count
        self.bastion_instance_type = bastion_instance_type
        self.bastion_sources = bastion_sources
        self.domain = domain
        self.nat = nat
        self.private_network = private_network

        # provider: GDH:
        self.deploy_stack = deploy_stack
        self.parent_stack = parent_stack

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
    def private_nat_gateway(self):
        return self.nat != 'disabled'

    @property
    def nat_per_az(self):
        return self.nat == 'per-az'

    @property
    def valid(self):
        name = (self.orbit and self.orbit.name) or '(no name)'

        valid = True
        if self.provider == 'spacel':
            valid = valid and self._valid_spacel(name)
        elif self.provider == 'gdh':
            valid = valid and self._valid_gdh(name)
        else:
            logger.error('App "%s" has invalid "provider": %s', name,
                         self.provider)
            valid = False
        return valid

    def _valid_spacel(self, name):
        valid = True
        if self.bastion_instance_type not in INSTANCE_TYPES:
            logger.error('App "%s" has invalid "bastion_instance_type": %s',
                         name, self.provider)
            valid = False

        if self.nat not in NAT_CONFIGURATIONS:
            logger.error('App "%s" has invalid "nat": %s',
                         name, self.provider)
            valid = False
        return valid

    def _valid_gdh(self, name):
        valid = True
        if not self.deploy_stack:
            logger.error('App "%s" is missing "deploy_stack".', name)
            valid = False
        if not self.parent_stack:
            logger.error('App "%s" is missing "parent_stack".', name)
            valid = False
        return valid


class OrbitRegionAz(object):
    def __init__(self,
                 private_elb_subnet=None,
                 private_instance_subnet=None,
                 public_elb_subnet=None,
                 public_instance_subnet=None):
        self.private_elb_subnet = private_elb_subnet
        self.private_instance_subnet = private_instance_subnet
        self.public_elb_subnet = public_elb_subnet
        self.public_instance_subnet = public_instance_subnet
