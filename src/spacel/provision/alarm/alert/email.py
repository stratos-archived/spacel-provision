import logging
from spacel.provision import clean_name

logger = logging.getLogger('spacel.provision.alarms.alerts.email')


class EmailAlerts(object):
    """
    Dispatches alert via email.
    This is built into SNS.
    """

    @staticmethod
    def resource_name(name):
        return 'AlertEmail%sTopic' % clean_name(name)

    def add_alerts(self, template, name, params):
        addresses = params.get('addresses')
        if not addresses:
            logger.warn('Email alert %s is missing "addresses".', name)
            return False
        if isinstance(addresses, str):
            addresses = addresses.split(',')

        resources = template['Resources']
        resource_name = self.resource_name(name)
        resources[resource_name] = {
            'Type': 'AWS::SNS::Topic',
            'Properties': {
                'Subscription': [{'Endpoint': e, 'Protocol': 'email'}
                                 for e in addresses],
                'DisplayName': {'Fn::Join': [
                    ' ', [
                        {'Ref': 'AWS::StackName'},
                        'CloudWatchEmailAlarms']
                ]}
            }
        }
        return True
