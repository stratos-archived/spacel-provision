import os


class SpaceService(object):
    def __init__(self, name, unit_file, environment=None):
        self.name = name
        self.unit_file = unit_file
        self.environment = environment or {}


class SpaceDockerService(SpaceService):
    def __init__(self, name, image, ports=None, volumes=None, environment=None):
        super(SpaceDockerService, self).__init__(name, None, environment)
        self.image = image
        self.ports = ports or {}
        self.volumes = volumes or {}

    @property
    def unit_file(self):
        name_base = os.path.splitext(self.name)[0]
        docker_run_flags = '--env-file /files/%s.env' % name_base
        docker_run_flags += self._dict_flags('p', self.ports)
        docker_run_flags += self._dict_flags('v', self.volumes)

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
""".format(self.name, self.image, docker_run_flags)

    @unit_file.setter
    def unit_file(self, value):
        pass

    @staticmethod
    def _dict_flags(flag, items):
        if not items:
            return ''
        pad_flag = ' -%s ' % flag
        return pad_flag + pad_flag.join(['%s:%s' % (k, v)
                                         for k, v in items.items()])
