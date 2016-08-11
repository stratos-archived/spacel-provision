from mock import MagicMock
import unittest

from spacel.aws import AmiFinder
from spacel.model import Orbit
from spacel.model.orbit import BASTION_INSTANCE_COUNT
from spacel.provision.template.bastion import BastionTemplate
from test.provision.template import SUBNETS

REGION = 'us-east-1'


class TestBastionTemplate(unittest.TestCase):
    def setUp(self):
        self.ami_finder = MagicMock(spec=AmiFinder)
        self.cache = BastionTemplate({}, self.ami_finder)
        base_template = self.cache.get('asg-bastion')
        self.base_resources = len(base_template['Resources'])
        self.orbit = Orbit({})
        self.orbit._public_instance_subnets = {REGION: SUBNETS}

    def test_bastion(self):
        bastion = self.cache.bastion(self.orbit, REGION)

        bastion_resources = len(bastion['Resources'])
        self.assertEquals(self.base_resources, bastion_resources)

    def test_bastion_multi_eip(self):
        self.orbit._params[REGION] = {BASTION_INSTANCE_COUNT: 2}

        bastion = self.cache.bastion(self.orbit, REGION)

        bastion_resources = len(bastion['Resources'])
        self.assertEquals(self.base_resources + 1, bastion_resources)
