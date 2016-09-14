from collections import defaultdict
import logging

logger = logging.getLogger('spacel')

DEFAULTS = 'defaults'

PRIVATE_NETWORK = 'private_network'

BASTION_INSTANCE_COUNT = 'bastion_instance_count'
BASTION_INSTANCE_TYPE = 'bastion_instance_type'
BASTION_SOURCE = 'bastion_source'
NAT_PER_AZ = 'nat_per_az'
PROVIDER = 'provider'
REGIONS = 'regions'

GDH_PARENT = 'parent_stack'
GDH_DEPLOY = 'deploy_stack'


class Orbit(object):
    DEFAULT_VALUES = {
        PRIVATE_NETWORK: '192.168',
        BASTION_INSTANCE_COUNT: 1,
        BASTION_INSTANCE_TYPE: 't2.nano',
        BASTION_SOURCE: '0.0.0.0/0',
        NAT_PER_AZ: False,
        PROVIDER: 'spacel'
    }

    def __init__(self, params):
        self.name = params.get('name', 'test')
        self.domain = params.get('domain', '')
        self._params = params

        # Queried from EC2:
        self._azs = {}

        # Output from VPC:
        self._vpc_ids = {}
        self._nat_eips = defaultdict(dict)
        self._public_instance_subnets = defaultdict(dict)
        self._public_elb_subnets = defaultdict(dict)
        self._private_instance_subnets = defaultdict(dict)
        self._private_elb_subnets = defaultdict(dict)
        self._private_cache_subnet_groups = {}
        self._private_rds_subnet_groups = {}
        self._public_rds_subnet_groups = {}

        # Output from Bastion:
        self._bastion_eips = defaultdict(dict)
        self._bastion_sgs = {}

    @property
    def regions(self):
        return self._params.get(REGIONS, ())

    def azs(self, region):
        return self._azs.get(region, ())

    def get_param(self, region, key):
        region_map = self._params.get(region)
        if region_map:
            region_value = region_map.get(key)
            if region_value is not None:
                return region_value

        defaults_map = self._params.get(DEFAULTS)
        if defaults_map:
            defaults_value = defaults_map.get(key)
            if defaults_value is not None:
                return defaults_value
        return self.DEFAULT_VALUES.get(key)

    def vpc_id(self, region):
        return self._vpc_ids.get(region)

    def bastion_sg(self, region):
        return self._bastion_sgs.get(region)

    # TODO: why isn't this a tuple like subnets?
    def bastion_eips(self, region):
        return self._bastion_eips.get(region, {})

    def public_instance_subnets(self, region):
        return self._public_instance_subnets.get(region, ())

    def private_instance_subnets(self, region):
        return self._private_instance_subnets.get(region, ())

    def public_elb_subnets(self, region):
        return self._public_elb_subnets.get(region, ())

    def private_elb_subnets(self, region):
        return self._private_elb_subnets.get(region, ())

    def private_cache_subnet_group(self, region):
        return self._private_cache_subnet_groups.get(region)

    def private_rds_subnet_group(self, region):
        return self._private_rds_subnet_groups.get(region)

    def public_rds_subnet_group(self, region):
        return self._public_rds_subnet_groups.get(region)
