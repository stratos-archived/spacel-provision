import logging
import os

import six

logger = logging.getLogger('spacel.model.app')


class SpaceApp(object):
    def __init__(self, orbit, name, regions=None):
        self.orbit = orbit
        self.name = name

        if regions:
            self.regions = {}
            for region in regions:
                if region in orbit.regions:
                    self.regions[region] = SpaceAppRegion()
                    continue

                logger.warn(
                    'App "%s" has invalid region "%s". Valid regions: %s',
                    name, region, ', '.join(orbit.regions))
        else:
            self.regions = {region: SpaceAppRegion()
                            for region in orbit.regions}

    @property
    def valid(self):
        if not self.name or not self.regions:
            return False
        return True

        # super(SpaceApp, self).__init__(params)
        # self.hostnames = self._params.get('hostnames', ())
        # self.instance_type = self._params.get('instance_type', 't2.nano')
        # self.instance_min = self._params.get('instance_min', 1)
        # self.instance_max = self._params.get('instance_max', 2)
        # self.health_check = self._params.get('health_check', 'TCP:80')
        # self.local_health_check = self._params.get('health_check', 'TCP:80')
        #
        # self.instance_availability = self._params.get('instance_availability',
        #                                               'private')
        # self.elb_availability = self._params.get('elb_availability',
        #                                          'internet-facing')
        # self.loadbalancer = self.elb_availability != 'disabled'
        #
        # public_ports = self._params.get('public_ports', {80: {}})
        # self.public_ports = {port: SpaceServicePort(port, port_params)
        #                      for port, port_params in public_ports.items()}
        #
        # self.private_ports = self._params.get('private_ports', {})
        # self.volumes = self._params.get('volumes', {})
        #
        # self.services = {}
        # services = self._params.get('services', {})
        # for service_name, service_params in services.items():
        #     if '.' not in service_name:
        #         service_name += '.service'
        #     service_env = service_params.get('environment', {})
        #     unit_file = service_params.get('unit_file')
        #     if unit_file:
        #         non_docker = SpaceService(service_name, unit_file, service_env)
        #         self.services[service_name] = non_docker
        #         continue
        #
        #     docker_image = service_params.get('image')
        #     if docker_image:
        #         ports = service_params.get('ports', {})
        #         volumes = service_params.get('volumes', {})
        #         docker = SpaceDockerService(service_name, docker_image, ports,
        #                                     volumes, service_env)
        #         self.services[service_name] = docker
        #         continue
        #
        #     logger.warning('Invalid service: %s', service_name)
        #
        # self.files = {}
        # files = self._params.get('files', {})
        # for file_name, file_params in files.items():
        #     if isinstance(file_params, six.string_types):
        #         encoded_body = base64_encode(file_params.encode('utf-8'))
        #         self.files[file_name] = {'body': encoded_body}
        #     else:
        #         self.files[file_name] = file_params
        #
        # self.alarms = self._params.get('alarms', {})
        # self.caches = self._params.get('caches', {})
        # self.databases = self._params.get('databases', {})
        # self.spot = self._spot(self._params)

    @staticmethod
    def _spot(params):
        spot = params.get('spot')
        if isinstance(spot, bool) and spot:
            return {}
        elif isinstance(spot, six.string_types) and bool(spot):
            return {}
        elif isinstance(spot, dict):
            return spot
        else:
            return None

    @property
    def full_name(self):
        return '%s-%s' % (self.orbit.name, self.name)


class SpaceAppRegion(object):
    def __init__(self,
                 health_check='TCP:80',
                 instance_max=2,
                 instance_min=1,
                 instance_type='t2.nano',
                 local_health_check='TCP:80'):
        self.health_check = health_check
        self.instance_max = instance_max
        self.instance_min = instance_min
        self.instance_type = instance_type
        self.local_health_check = local_health_check


class SpaceServicePort(object):
    def __init__(self, port, params=None):
        params = params or {}
        self.scheme = params.get('scheme', self._scheme(port))

        self.internal_port = params.get('internal_port', port)
        self.internal_scheme = params.get('internal_scheme',
                                          self._scheme(self.internal_port))

        self.sources = params.get('sources', ('0.0.0.0/0',))
        self.certificate = params.get('certificate')

    @staticmethod
    def _scheme(port):
        if str(port) == '443':
            return 'HTTPS'
        return 'HTTP'


