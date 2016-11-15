import logging

logger = logging.getLogger('spacel.model.app')


class SpaceApp(object):
    """
    Configuration of a hosted application.
    Contains SpaceAppRegion entries for each configured region.
    """

    def __init__(self, orbit, name, regions=None):
        self.orbit = orbit
        self.name = name

        if regions:
            self.regions = {}
            for region in regions:
                orbit_region = orbit.regions.get(region)
                if orbit_region:
                    self.regions[region] = SpaceAppRegion(self, orbit_region)
                    continue

                logger.warn(
                    'App "%s" has invalid region "%s". Valid regions: %s',
                    name, region, ', '.join(orbit.regions))
        else:
            self.regions = {region: SpaceAppRegion(self, orbit_region)
                            for region, orbit_region in orbit.regions.items()}

    @property
    def valid(self):
        if not self.name or not self.regions:
            return False
        return True

    @property
    def full_name(self):
        return '%s-%s' % (self.orbit.name, self.name)


class SpaceAppRegion(object):
    def __init__(self,
                 app,
                 orbit_region,
                 elb_availability='internet-facing',
                 health_check='TCP:80',
                 hostnames=(),
                 instance_availability='private',
                 instance_max=2,
                 instance_min=1,
                 instance_type='t2.nano',
                 local_health_check='TCP:80',
                 spot=None):
        self.app = app
        self.orbit_region = orbit_region
        self.region = orbit_region.region
        self.elb_availability = elb_availability
        self.health_check = health_check
        self.hostnames = hostnames
        self.instance_availability = instance_availability
        self.instance_max = instance_max
        self.instance_min = instance_min
        self.instance_type = instance_type
        self.local_health_check = local_health_check
        self.spot = spot
        self.alarms = {}
        self.caches = {}
        self.databases = {}
        self.files = {}
        self.private_ports = {}
        self.public_ports = {}
        self.services = {}
        self.volumes = {}

    @property
    def load_balancer(self):
        return self.elb_availability != 'disabled'


class SpaceServicePort(object):
    def __init__(self,
                 port,
                 certificate=None,
                 internal_port=None,
                 internal_scheme=None,
                 scheme=None,
                 sources=('0.0.0.0/0',)
                 ):
        self.certificate = certificate
        internal_port = internal_port or port
        self.internal_port = internal_port
        self.internal_scheme = internal_scheme or self._scheme(internal_port)
        self.scheme = scheme or self._scheme(port)
        self.sources = sources

    @staticmethod
    def _scheme(port):
        if str(port) == '443':
            return 'HTTPS'
        return 'HTTP'
