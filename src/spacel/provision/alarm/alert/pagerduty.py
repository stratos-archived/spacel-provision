import logging
from spacel.provision import clean_name

logger = logging.getLogger('spacel.provision.alarms.alerts.pagerduty')


class PagerDutyAlerts(object):
    """
    Dispatches alert via PagerDuty.
    PagerDuty provides an SNS compatible WebHook.
    """

    def __init__(self, default_url):
        self._default_url = default_url

    def add_alerts(self, template, name, params):
        url = self._get_url(params)
        if not url:
            logger.warn('PagerDuty alert %s is missing "url".', name)
            return False

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
        return True

    def _get_url(self, params):
        # TODO: PagerDuty smarts: if URL isn't found, lookup/register using API
        return params.get('url', self._default_url)

    @staticmethod
    def resource_name(name):
        return 'AlertPagerDuty%sTopic' % clean_name(name)
