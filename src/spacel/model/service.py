import os


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
