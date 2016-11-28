import unittest

import requests

from spacel.aws import ClientCache
from spacel.cli.provision import provision
from spacel.main import setup_logging
from spacel.model import (Orbit, SpaceApp, SpaceDockerService, SpaceServicePort,
                          SpaceService, OrbitRegion, SpaceAppRegion)
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

APP_NAME = 'laika'
ORBIT_NAME = 'sl-test'
ORBIT_REGION = 'us-east-1'
ORBIT_DOMAIN = 'pebbledev.com'
BASTION_INSTANCE_COUNT = 0

SECOND_REGION = 'us-west-2'


class BaseIntegrationTest(unittest.TestCase):
    APP_HOSTNAME = '%s-%s.%s' % (APP_NAME, ORBIT_NAME, ORBIT_DOMAIN)
    APP_VERSION = '0.3.0'
    UPGRADE_VERSION = '0.1.1'
    APP_URL = 'https://%s' % APP_HOSTNAME

    @classmethod
    def setUpClass(cls):
        setup_logging()

    def setUp(self):
        self.orbit = Orbit(
            name=ORBIT_NAME,
            regions=[ORBIT_REGION],
            domain=ORBIT_DOMAIN,
            bastion_instance_count=BASTION_INSTANCE_COUNT
        )
        self.app = SpaceApp(
            self.orbit,
            name=APP_NAME,
            health_check='HTTP:80/'
        )
        self._setup_app_regions()

        self.clients = ClientCache()
        self.ssh_db = SpaceSshDb(self.clients)

    def _setup_app_regions(self):
        self.docker_service = SpaceDockerService('laika.service', None,
                                                 ports={80: 8080})
        http_port = SpaceServicePort(80)
        https_port = SpaceServicePort(443, internal_port=80)
        for app_region in self.app.regions.values():
            app_region.services['laika'] = self.docker_service
            app_region.public_ports[80] = http_port
            app_region.public_ports[443] = https_port
        self.image()

    def image(self, version=APP_VERSION):
        docker_tag = 'pebbletech/spacel-laika:%s' % version
        for app_region in self.app.regions.values():
            app_region.services['laika'].image = docker_tag

    def provision(self, expected=0):
        result = provision(self.app,
                           lambda_bucket='spacel-pebbledev',
                           lambda_region='us-east-1',
                           spacel_agent_channel='latest')
        self.assertEquals(expected, result)
        for user, key in FORENSICS_USERS.items():
            self.ssh_db.add_key(self.orbit, user, key)
            self.ssh_db.grant(self.app, user)

    def _second_region(self):
        self.orbit_region_2 = OrbitRegion(
            self.orbit, SECOND_REGION,
            domain=ORBIT_DOMAIN,
            bastion_instance_count=BASTION_INSTANCE_COUNT
        )
        self.orbit.regions[SECOND_REGION] = self.orbit_region_2
        self.app.regions[SECOND_REGION] = SpaceAppRegion(self.app,
                                                         self.orbit_region_2)
        self._setup_app_regions()

    def _app_eip_only(self):
        for app_region in self.app.regions.values():
            app_region.instance_max = 1
            app_region.elb_availability = 'disabled'
            app_region.instance_availability = 'internet-facing'
            app_region.elastic_ips = True

    @staticmethod
    def _get(url, https=True):
        full_url = '%s/%s' % (BaseIntegrationTest.APP_URL, url)
        if not https:
            full_url = full_url.replace('https://', 'http://')
        return requests.get(full_url)

    @staticmethod
    def _post(url):
        full_url = '%s/%s' % (BaseIntegrationTest.APP_URL, url)
        return requests.post(full_url)

    def _verify_counter(self, counter_type, expected_count=0, post_count=10):
        counter_url = '%s/counter' % counter_type
        r = self._get(counter_url)
        count = r.json()['count']
        self.assertTrue(count >= expected_count)
        for i in range(post_count):
            r = self._post(counter_url)
            count = r.json()['count']
        return count

    def _set_unit_file(self, unit_file):
        for app_region in self.app.regions.values():
            app_region.services['laika'] = SpaceService('laika.service',
                                                        unit_file)
