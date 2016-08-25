from mock import MagicMock
import unittest

from spacel.aws import AmiFinder
from spacel.model import Orbit, SpaceApp, SpaceDockerService
from spacel.provision.template.app import AppTemplate
from spacel.provision.alarm import AlertFactory, TriggerFactory
from test.provision.template import SUBNETS

REGION = 'us-east-1'


class TestAppTemplate(unittest.TestCase):
    def setUp(self):
        self.ami_finder = MagicMock(spec=AmiFinder)
        self.alerts = MagicMock(spec=AlertFactory)
        self.triggers = MagicMock(spec=TriggerFactory)
        self.cache = AppTemplate(self.ami_finder, self.alerts, self.triggers)
        base_template = self.cache.get('elb-service')
        self.base_resources = len(base_template['Resources'])
        self.orbit = Orbit({
            'domain': 'test.com'
        })
        self.orbit._public_elb_subnets = {REGION: SUBNETS}
        self.orbit._private_elb_subnets = {REGION: SUBNETS}
        self.orbit._private_instance_subnets = {REGION: SUBNETS}
        self.app = SpaceApp(self.orbit, {
            'name': 'app'
        })

    def test_app(self):
        app = self.cache.app(self.app, REGION)

        app_resources = len(app['Resources'])
        self.assertEquals(self.base_resources, app_resources)
        params = app['Parameters']
        resources = app['Resources']

        self.assertEquals(params['VirtualHostDomain']['Default'], 'test.com.')
        self.assertEquals(params['VirtualHost']['Default'], 'app-test.test.com')

        block_devs = resources['Lc']['Properties']['BlockDeviceMappings']
        self.assertEquals(1, len(block_devs))

    def test_app_domain(self):
        self.app.hostnames = ('app.test.com',)

        app = self.cache.app(self.app, REGION)

        params = app['Parameters']
        self.assertEquals(params['VirtualHostDomain']['Default'], 'test.com.')
        self.assertEquals(params['VirtualHost']['Default'], 'app.test.com')

    def test_app_private_ports(self):
        self.app.private_ports = {123: ['TCP']}

        app = self.cache.app(self.app, REGION)

        self.assertIn('PrivatePort123TCP', app['Resources'])

    def test_app_instance_storage(self):
        self.app.instance_type = 'c1.medium'

        app = self.cache.app(self.app, REGION)

        block_devs = app['Resources']['Lc']['Properties']['BlockDeviceMappings']
        self.assertEquals(2, len(block_devs))

    def test_user_data(self):
        params = {}

        user_data = self.cache._user_data(params, self.app)

        self.assertEquals('', user_data)

    def test_user_data_services(self):
        params = {'VolumeSupport': {}}
        self.app.services = {
            'test.service': SpaceDockerService('test', 'test/test',
                                               environment={'FOO': 'bar'})
        }

        user_data = self.cache._user_data(params, self.app)

        self.assertIn('"test.service"', user_data)
        self.assertNotIn('Default', params['VolumeSupport'])

    def test_user_data_volumes(self):
        params = {'VolumeSupport': {}}
        self.app.volumes = {'test': {'count': 2, 'size': 2}}

        user_data = self.cache._user_data(params, self.app)

        self.assertIn('"test"', user_data)
        self.assertEquals(params['VolumeSupport']['Default'], 'true')
