import unittest
import logging

from spacel.aws import ClientCache
from spacel.main import provision
from spacel.model import Orbit, SpaceApp
from spacel.model.orbit import (NAME, DOMAIN, REGIONS)
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
            DOMAIN: 'pebbledev.com',
            REGIONS: ['us-east-1']
        }
        self.app_params = {
            'name': 'test-app',
            'health_check': 'HTTP:80/',
            'instance_type': 't2.nano',
            'instance_min': 1,
            'instance_max': 1,
            'services': {
                'laika': {
                    'image': 'pebbletech/spacel-laika:latest',
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
        self.clients = ClientCache()
        self.ssh_db = SpaceSshDb(self.clients)

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
