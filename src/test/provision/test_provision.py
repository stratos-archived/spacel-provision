from mock import MagicMock
import unittest

from spacel.aws import ClientCache
from spacel.model import Orbit, SpaceApp
from spacel.provision.changesets import ChangeSetEstimator
from spacel.provision.provision import CloudProvisioner
from spacel.provision.template import AppTemplate
from spacel.provision.s3 import TemplateUploader

REGIONS = ('us-east-1', 'us-west-2')


class TestCloudProvisioner(unittest.TestCase):
    def setUp(self):
        self.clients = MagicMock(spec=ClientCache)
        self.change_sets = MagicMock(spec=ChangeSetEstimator)
        self.templates = MagicMock(spec=TemplateUploader)
        self.app_template = MagicMock(spec=AppTemplate)
        self.app_template.app.return_value = {}

        self.provisioner = CloudProvisioner(self.clients, self.change_sets,
                                            self.templates,
                                            self.app_template)
        self.provisioner._wait_for_updates = MagicMock()
        self.provisioner._stack = MagicMock()
        self.provisioner._delete_stack = MagicMock()

        self.orbit = Orbit({
            'regions': REGIONS
        })
        self.app = SpaceApp(self.orbit, {})

    def test_app_create(self):
        self.provisioner._stack.return_value = 'create'
        self.provisioner.app(self.app)

        self.assertEquals(len(REGIONS), self.provisioner._stack.call_count)
        self.assertEquals(1, self.provisioner._wait_for_updates.call_count)

    def test_app_delete(self):
        self.provisioner._stack.return_value = 'delete'
        self.provisioner.delete_app(self.app)

        self.assertEquals(len(REGIONS),
                          self.provisioner._delete_stack.call_count)
        self.assertEquals(1, self.provisioner._wait_for_updates.call_count)
