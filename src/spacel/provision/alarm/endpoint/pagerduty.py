import logging
from spacel.provision import clean_name
from spacel.provision.alarm.actions import ACTIONS_NONE, ACTIONS_OK_ALARM

logger = logging.getLogger('spacel.provision.alarm.endpoint.pagerduty')


class PagerDutyEndpoints(object):
    """
    Dispatches via PagerDuty.
    PagerDuty provides an SNS compatible WebHook.
    """

    def __init__(self, default_url):
        self._default_url = default_url

    def add_endpoints(self, template, name, params):
        url = self._get_url(params)
        if not url:
            logger.warn('PagerDuty endpoint %s is missing "url".', name)
            return ACTIONS_NONE

        resources = template['Resources']
        resource_name = self.resource_name(name)
        resources[resource_name] = {
            'Type': 'AWS::SNS::Topic',
            'Properties': {
                'Subscription': [{'Endpoint': url, 'Protocol': 'https'}],
                'DisplayName': {'Fn::Join': [
                    ' ', [
                        {'Ref': 'AWS::StackName'},
                        'CloudWatchEmailAlarms']
                ]}
            }
        }
        return ACTIONS_OK_ALARM

    def _get_url(self, params):
        # TODO: PagerDuty smarts: if URL isn't found, lookup/register using API
        return params.get('url', self._default_url)

    @staticmethod
    def resource_name(name):
        return 'EndpointPagerDuty%sTopic' % clean_name(name)
