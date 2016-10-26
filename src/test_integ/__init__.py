import unittest
import logging

from spacel.aws import ClientCache
from spacel.main import provision
from spacel.model import Orbit, SpaceApp
from spacel.model.orbit import (NAME, BASTION_INSTANCE_COUNT, DOMAIN, REGIONS)
from spacel.user import SpaceSshDb

FORENSICS_USERS = {
    'pwagner':
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC46uFbuAy8posO4dzLSIeiaeI8xM5GK'
        'WuuTIuYIGm/xwML+GWq5lgEmfAx7tWSaoPbkr5V65swkJgF3XMOYwzAvu/9ySS5o3+4N+'
        'jzoYhVHae7EnQFYBJt+GeCJ2gZyz1wYu0UdawCHk9yLWLwIpM8QkVLvo0NCYh4X+7JsmC'
        'WQqauZdF+NG3JwxiYSd95HEHuuQO1CxBe084Kc4QRMMyeVI45jhVXd9fH2hwKxK0XylrX'
        'qwWKzRn6/hZiJI4r5MqCUZsxOZPFYQkfvJ/Rhc4tFRKk8TdfBuPdqMX7HwzJypUVX/ajF'
        'Hwm1BJIzo1alidHU7rzEs510JKzEmHI/vUT'
}


class BaseIntegrationTest(unittest.TestCase):
    ORBIT_NAME = 'sl-test'
    APP_NAME = 'laika'
    APP_DOMAIN = 'pebbledev.com'
    APP_HOSTNAME = '%s-%s.%s' % (APP_NAME, ORBIT_NAME, APP_DOMAIN)
    APP_VERSION = '0.1.0'

    @classmethod
    def setUpClass(cls):
        log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=log_format)
        logging.getLogger('boto3').setLevel(logging.CRITICAL)
        logging.getLogger('botocore').setLevel(logging.CRITICAL)
        logging.getLogger('paramiko').setLevel(logging.CRITICAL)
        logging.getLogger('requests').setLevel(logging.CRITICAL)

        logging.getLogger('spacel').setLevel(logging.DEBUG)

    def setUp(self):
        self.orbit_params = {
            NAME: BaseIntegrationTest.ORBIT_NAME,
            DOMAIN: BaseIntegrationTest.APP_DOMAIN,
            REGIONS: ['us-east-1'],
            'defaults': {
                BASTION_INSTANCE_COUNT: 0
            }
        }

        self.app_params = {
            'name': BaseIntegrationTest.APP_NAME,
            'health_check': 'HTTP:80/',
            'instance_type': 't2.nano',
            'instance_min': 1,
            'instance_max': 2,
            'services': {
                'laika': {
                    'ports': {
                        '80': 8080
                    }
                }
            },
            'public_ports': {
                '80': {
                    'sources': ['0.0.0.0/0']
                },
                '443': {
                    'sources': ['0.0.0.0/0'],
                    'internal_port': 80
                }
            }
        }
        self.image()
        self.clients = ClientCache()
        self.ssh_db = SpaceSshDb(self.clients)

    def image(self, version=APP_VERSION):
        docker_tag = 'pebbletech/spacel-laika:%s' % version
        self.app_params['services']['laika']['image'] = docker_tag

    def orbit(self):
        return Orbit(self.orbit_params)

    def app(self):
        return SpaceApp(self.orbit(), self.app_params)

    def provision(self, expected=0):
        app = self.app()
        result = provision(app)
        self.assertEquals(expected, result)
        for user, key in FORENSICS_USERS.items():
            self.ssh_db.add_key(app.orbit, user, key)
            self.ssh_db.grant(app, user)
        return app
