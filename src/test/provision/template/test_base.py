from mock import MagicMock
import unittest

from spacel.aws import AmiFinder
from spacel.provision.template.base import BaseTemplateCache
from test.provision.template import SUBNET_1, SUBNET_2, SUBNET_3, SUBNETS

NAME = 'test'


class TestBaseTemplateCache(unittest.TestCase):
    def setUp(self):
        self.ami_finder = MagicMock(spec=AmiFinder)
        self.cache = BaseTemplateCache({}, self.ami_finder)

    def test_get_load(self):
        tables = self.cache.get('tables')
        self.assertIsNotNone(tables)

    def test_get_cached(self):
        self.cache.get('tables')
        tables = self.cache.get('tables')
        self.assertIsNotNone(tables)

    def test_get_name_tag(self):
        name = self.cache._get_name_tag({
            'Tags': [
                {'Key': 'Foo', 'Value': 'Bar'},
                {'Key': 'Name', 'Value': NAME}
            ]
        })
        self.assertEquals(NAME, name)

    def test_get_name_tag_miss(self):
        name = self.cache._get_name_tag({
            'Tags': [
                {'Key': 'Foo', 'Value': 'Bar'}
            ]
        })
        self.assertIsNone(name)

    def test_subnet_params(self):
        params = {
            'TestSubnet01': {}
        }

        self.cache._subnet_params(params, 'Test', SUBNETS)

        self.assertEquals(len(SUBNETS), len(params))
        self.assertEquals(SUBNET_1, params['TestSubnet01']['Default'])
        self.assertEquals(SUBNET_2, params['TestSubnet02']['Default'])
        self.assertEquals(SUBNET_3, params['TestSubnet03']['Default'])

    def test_asg_params(self):
        asg_zones = []
        resources = {
            'Asg': {
                'Properties': {
                    'VPCZoneIdentifier': asg_zones
                }
            }
        }

        self.cache._asg_subnets(resources, 'Test', SUBNETS)

        self.assertEquals(len(SUBNETS) - 1, len(asg_zones))

    def test_elb_params(self):
        elb_zones = []
        resources = {
            'Test': {
                'Properties': {
                    'Subnets': elb_zones
                }
            }
        }

        self.cache._elb_subnets(resources, 'Test', SUBNETS)

        self.assertEquals(len(SUBNETS) - 1, len(elb_zones))
