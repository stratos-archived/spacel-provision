import unittest
from mock import MagicMock

from spacel.provision.alarm.alert.factory import AlertFactory

FACTORY_TYPE = 'test'
ALERT_NAME = 'test-alert'


class TestAlertFactory(unittest.TestCase):
    def setUp(self):
        self.resources = {}
        self.template = {
            'Resources': self.resources
        }
        self.factory = MagicMock()

        self.alert = AlertFactory({
            FACTORY_TYPE: self.factory
        })

    def test_add_alerts_no_type(self):
        self.alert.add_alerts(self.template, {
            ALERT_NAME: {}
        })
        self.factory.add_alerts.assert_not_called()

    def test_add_alerts_invalid_type(self):
        self.alert.add_alerts(self.template, {
            ALERT_NAME: {
                'type': 'kaboom-missing'
            }
        })
        self.factory.add_alerts.assert_not_called()

    def test_add_alerts(self):
        alert_params = {'type': FACTORY_TYPE, 'foo': 'bar'}
        self.alert.add_alerts(self.template, {
            ALERT_NAME: alert_params
        })
        self.factory.add_alerts.assert_called_with(self.template, ALERT_NAME,
                                                   alert_params)
