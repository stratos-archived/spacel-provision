from mock import patch, MagicMock, ANY

from spacel.cli.provision import provision_services
from test import BaseSpaceAppTest, ORBIT_NAME, APP_NAME


class TestProvisionCommand(BaseSpaceAppTest):
    @patch('spacel.cli.provision.ClickHelper')
    @patch('spacel.cli.provision.provision')
    def test_provision_services_invalid_orbit(self, mock_provision,
                                              helper_factory):
        helper = MagicMock()
        orbit = MagicMock()
        orbit.valid = False
        helper.orbit.return_value = orbit
        helper.app.return_value = self.app
        helper_factory.return_value = helper

        provision_services(ORBIT_NAME, APP_NAME, (), None, None, None, None,
                           None, None, None, None, 'CRITICAL', None, False)
        mock_provision.assert_not_called()

    @patch('spacel.cli.provision.ClickHelper')
    @patch('spacel.cli.provision.provision')
    def test_provision_services_invalid_app(self, mock_provision,
                                            helper_factory):
        helper = MagicMock()
        helper.orbit.return_value = self.orbit
        app = MagicMock()
        app.valid = False
        helper.app.return_value = app
        helper_factory.return_value = helper

        provision_services(ORBIT_NAME, APP_NAME, (), None, None, None, None,
                           None, None, None, None, 'CRITICAL', None, False)
        mock_provision.assert_not_called()

    @patch('spacel.cli.provision.ClickHelper')
    @patch('spacel.cli.provision.provision')
    def test_provision_services(self, mock_provision, helper_factory):
        helper = MagicMock()
        helper.orbit.return_value = self.orbit
        helper.app.return_value = self.app
        helper_factory.return_value = helper

        provision_services(ORBIT_NAME, APP_NAME, (), None, None, None, None,
                           None, None, None, None, 'CRITICAL', None, False)
        mock_provision.assert_called_once_with(ANY, None, None, None, None,
                                               None, None, None, None, False)
