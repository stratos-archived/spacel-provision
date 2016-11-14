import logging
import os

import six

from spacel.model.base import BaseModelObject
from spacel.provision import base64_encode

logger = logging.getLogger('spacel.model.app')


class SpaceApp(BaseModelObject):
    def __init__(self, orbit, params=None):
        self.orbit = orbit
        super(SpaceApp, self).__init__(params)
        self.hostnames = self._params.get('hostnames', ())
        self.instance_type = self._params.get('instance_type', 't2.nano')
        self.instance_min = self._params.get('instance_min', 1)
        self.instance_max = self._params.get('instance_max', 2)
        self.health_check = self._params.get('health_check', 'TCP:80')
        self.local_health_check = self._params.get('health_check', 'TCP:80')

        self.instance_availability = self._params.get('instance_availability',
                                                      'private')
        self.elb_availability = self._params.get('elb_availability',
                                                 'internet-facing')
        self.loadbalancer = self.elb_availability != 'disabled'

        public_ports = self._params.get('public_ports', {80: {}})
        self.public_ports = {port: SpaceServicePort(port, port_params)
                             for port, port_params in public_ports.items()}

        self.private_ports = self._params.get('private_ports', {})
        self.volumes = self._params.get('volumes', {})

        self.services = {}
        services = self._params.get('services', {})
        for service_name, service_params in services.items():
            if '.' not in service_name:
                service_name += '.service'
            service_env = service_params.get('environment', {})
            unit_file = service_params.get('unit_file')
            if unit_file:
                non_docker = SpaceService(service_name, unit_file, service_env)
                self.services[service_name] = non_docker
                continue

            docker_image = service_params.get('image')
            if docker_image:
                ports = service_params.get('ports', {})
                volumes = service_params.get('volumes', {})
                docker = SpaceDockerService(service_name, docker_image, ports,
                                            volumes, service_env)
                self.services[service_name] = docker
                continue

            logger.warning('Invalid service: %s', service_name)

        self.files = {}
        files = self._params.get('files', {})
        for file_name, file_params in files.items():
            if isinstance(file_params, six.string_types):
                encoded_body = base64_encode(file_params.encode('utf-8'))
                self.files[file_name] = {'body': encoded_body}
            else:
                self.files[file_name] = file_params

        self.alarms = self._params.get('alarms', {})
        self.caches = self._params.get('caches', {})
        self.databases = self._params.get('databases', {})
        self.spot = self._spot(self._params)

    def _regions(self):
        orbit_regions = self.orbit.regions
        return super(SpaceApp, self)._regions(valid_regions=orbit_regions,
                                              default_regions=orbit_regions)

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


class SpaceService(object):
    def __init__(self, name, unit_file, environment=None):
        self.name = name
        self.unit_file = unit_file
        self.environment = environment or {}


class SpaceDockerService(SpaceService):
    def __init__(self, name, image, ports=None, volumes=None, environment=None):
        name_base = os.path.splitext(name)[0]
        docker_run_flags = '--env-file /files/%s.env' % name_base
        docker_run_flags += SpaceDockerService._dict_flags('p', ports)
        docker_run_flags += SpaceDockerService._dict_flags('v', volumes)

        unit_file = """[Unit]
Description={0}
Wants=spacel-agent.service

[Service]
User=space
TimeoutStartSec=0
Restart=always
StartLimitInterval=0
ExecStartPre=-/usr/bin/docker pull {1}
ExecStartPre=-/usr/bin/docker rm -f %n
ExecStart=/usr/bin/docker run --rm --name %n {2} {1}
ExecStop=/usr/bin/docker stop -t 2 %n
""".format(name, image, docker_run_flags)
        super(SpaceDockerService, self).__init__(name, unit_file, environment)

    @staticmethod
    def _dict_flags(flag, items):
        if not items:
            return ''
        pad_flag = ' -%s ' % flag
        return pad_flag + pad_flag.join(['%s:%s' % (k, v)
                                         for k, v in items.items()])
