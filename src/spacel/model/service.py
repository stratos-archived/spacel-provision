import os

import six


class SpaceService(object):
    def __init__(self, name, unit_file, environment=None, version=None):
        self.name = name
        self._unit_file = unit_file
        self.environment = environment or {}
        self.version = version

    @property
    def unit_file(self):
        if isinstance(self._unit_file, six.string_types):
            version = self.version or 'latest'
            return self._unit_file.replace('__VERSION__', version)
        return self._unit_file

    @unit_file.setter
    def unit_file(self, unit_file):
        self._unit_file = unit_file


class SpaceDockerService(SpaceService):
    def __init__(self, name, image, ports=None, volumes=None, environment=None,
                 version=None):
        super(SpaceDockerService, self).__init__(name, None, environment,
                                                 version)
        self.image = image
        self.ports = ports or {}
        self.volumes = volumes or {}

    @property
    def unit_file(self):
        name_base = os.path.splitext(self.name)[0]
        docker_run_flags = '--env-file /files/%s.env' % name_base
        docker_run_flags += self._dict_flags('p', self.ports)
        docker_run_flags += self._dict_flags('v', self.volumes)

        if ':' not in self.image:
            image = '%s:%s' % (self.image, self.version or 'latest')
        else:
            image = self.image

        return """[Unit]
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
""".format(self.name, image, docker_run_flags)

    @staticmethod
    def _dict_flags(flag, items):
        if not items:
            return ''
        pad_flag = ' -%s ' % flag
        return pad_flag + pad_flag.join(['%s:%s' % (k, v)
                                         for k, v in items.items()])
