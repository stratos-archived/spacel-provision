import logging
from spacel.provision import clean_name

logger = logging.getLogger('spacel.provision.alarm.endpoint.email')


class EmailEndpoints(object):
    """
    Dispatches via email.
    This is built into SNS.
    """

    @staticmethod
    def resource_name(name):
        return 'EndpointEmail%sTopic' % clean_name(name)

    def add_endpoints(self, template, name, params):
        addresses = params.get('addresses')
        if not addresses:
            logger.warn('Email endpoint %s is missing "addresses".', name)
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
                        'CloudWatchEmailEndpoint']
                ]}
            }
        }
        return True
