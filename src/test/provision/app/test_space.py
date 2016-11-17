from mock import MagicMock

from spacel.aws import ClientCache
from spacel.model import OrbitRegion, SpaceAppRegion
from spacel.provision.app.space import SpaceElevatorAppFactory
from spacel.provision.changesets import ChangeSetEstimator
from spacel.provision.s3 import TemplateUploader
from spacel.provision.template import AppTemplate
from test import BaseSpaceAppTest

OTHER_REGION = 'us-east-1'


class TestSpaceElevatorAppFactory(BaseSpaceAppTest):
    def setUp(self):
        super(TestSpaceElevatorAppFactory, self).setUp()
        self.clients = MagicMock(spec=ClientCache)
        self.change_sets = MagicMock(spec=ChangeSetEstimator)
        self.templates = MagicMock(spec=TemplateUploader)
        self.app_template = MagicMock(spec=AppTemplate)
        self.app_template.app.return_value = {'Spacel': 'Rules'}, {}

        self.provisioner = SpaceElevatorAppFactory(self.clients,
                                                   self.change_sets,
                                                   self.templates,
                                                   self.app_template)
        self.provisioner._wait_for_updates = MagicMock()
        self.provisioner._stack = MagicMock()
        self.provisioner._delete_stack = MagicMock()

        other_region = OrbitRegion(self.orbit, OTHER_REGION)
        self.orbit.regions[OTHER_REGION] = other_region
        self.app.regions[OTHER_REGION] = SpaceAppRegion(self.app, other_region)

    def test_app_create(self):
        self.provisioner._stack.return_value = 'create'
        self.provisioner.app(self.app)

        self.assertEquals(2, self.provisioner._stack.call_count)
        self.assertEquals(1, self.provisioner._wait_for_updates.call_count)

    def test_app_delete(self):
        self.provisioner._stack.return_value = 'delete'
        self.provisioner.delete_app(self.app)

        self.assertEquals(2, self.provisioner._delete_stack.call_count)
        self.assertEquals(1, self.provisioner._wait_for_updates.call_count)

    def test_app_syntax_rejected(self):
        self.app_template.app.return_value = False, False
        self.provisioner.app(self.app)

        self.provisioner._stack.assert_not_called()
        self.assertEquals(1, self.provisioner._wait_for_updates.call_count)
