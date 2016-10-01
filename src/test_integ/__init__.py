import unittest
import logging

from spacel.aws import ClientCache
from spacel.main import provision
from spacel.model import Orbit, SpaceApp
from spacel.model.orbit import (NAME, DOMAIN, REGIONS)


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
                'http-env-echo': {
                    'image': 'pwagner/http-env-echo',
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

    def orbit(self):
        return Orbit(self.orbit_params)

    def app(self):
        return SpaceApp(self.orbit(), self.app_params)

    def provision(self, expected=0):
        app = self.app()
        result = provision(app)
        self.assertEquals(expected, result)
        return app
