import json
import logging
import six
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import HTTPError

from spacel.provision import clean_name
from spacel.provision.alarm.actions import ACTIONS_NONE, ACTIONS_OK_ALARM

logger = logging.getLogger('spacel.provision.alarm.endpoint.pagerduty')

PD_API_BASE = 'https://api.pagerduty.com/'
PD_EVENTS_BASE = 'https://events.pagerduty.com/adapter/cloudwatch_sns/v1/'
APPLICATION_JSON = 'application/json; charset=utf-8'

# https://support.pagerduty.com/hc/en-us/articles/219898067-Create-a-Vendor-Specific-Service-with-the-API
VENDOR_CLOUDWATCH = 'PZQ6AUS'

INTEGRATION_TYPE = 'event_transformer_api_inbound_integration_reference'


class PagerDutyEndpoints(object):
    """
    Dispatches via PagerDuty.
    PagerDuty provides an SNS compatible WebHook.
    """

    def __init__(self, default_url, pd_api_key):
        self._default_url = default_url
        self._pd_headers = {}
        if pd_api_key:
            self._pd_headers['Authorization'] = 'Token token=%s' % pd_api_key

    @staticmethod
    def resource_name(name):
        return 'EndpointPagerDuty%sTopic' % clean_name(name)

    def add_endpoints(self, template, name, params):
        url = self._get_url(template, params)
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
                        'CloudWatchPagerDutyAlarms']
                ]}
            }
        }
        return ACTIONS_OK_ALARM

    def _get_url(self, template, params):
        parameters = template['Parameters']
        service = parameters['Service']['Default']
        orbit = parameters['Orbit']['Default']
        pd_service_name = '%s (%s)' % (service, orbit)

        url = params.get('url')
        if url:
            return url

        # Without PagerDuty API key we can't continue:
        if not self._pd_headers:
            return self._default_url

        # Service can be specified by id:
        service_id = params.get('service')
        if service_id:
            integration_key = self._integration_key(service_id)
            if integration_key:
                return '%s/%s' % (PD_EVENTS_BASE, integration_key)

        # Escalation policy can be specified by id:
        escalation = params.get('escalation_policy')
        if escalation:
            url = '/escalation_policies/%s?include[]=service' % escalation
            policy = self._pd_api(url)
            if not policy:
                logger.warn('Escalation policy %s not found.', escalation)
            else:
                policy = policy['escalation_policy']
                logger.debug('Using escalation policy "%s" (%s).',
                             policy['summary'],
                             escalation)

                service_id = self._service_id(policy, escalation,
                                              pd_service_name)
                if service_id:
                    integration_key = self._integration_key(service_id)
                    if integration_key:
                        return '%s/%s' % (PD_EVENTS_BASE, integration_key)

        return self._default_url

    def _integration_key(self, service_id):
        # Fetch service details:
        service = self._pd_api('/services/%s' % service_id)
        if not service:
            logger.warn('Invalid service "%s".', service_id)
            return None
        service = service['service']

        # Check for existing integration:
        for integration in service['integrations']:
            if integration['type'] == INTEGRATION_TYPE:
                integration_id = integration['id']
                logger.debug('Found existing integration "%s".', integration_id)

                integration_url = ('/services/%s/integrations/%s'
                                   % (service_id, integration_id))
                integration = self._pd_api(integration_url)
                return integration['integration']['integration_key']

        logger.debug('Integration not found, creating...')

        integration_params = {
            'type': INTEGRATION_TYPE,
            'vendor': {
                'type': 'vendor_reference',
                'id': VENDOR_CLOUDWATCH
            }
        }
        new_integration = self._pd_api('/services/%s/integrations' % service_id,
                                       method='POST',
                                       data={
                                           'integration': integration_params
                                       })
        new_integration = new_integration['integration']
        return new_integration['integration_key']

    def _service_id(self, policy, escalation, service_name):
        # Check for existing service:
        for service in policy.get('services', ()):
            if service['summary'] == service_name:
                service_url = service['self']
                service_id = service_url.split('/')[-1]
                logger.debug('Found existing service "%s" (%s).', service_name,
                             service_id)
                return service_id

        logger.debug('Service not found, creating...')
        service_params = {
            'name': service_name,
            'type': 'service',
            'escalation_policy': {
                'id': escalation,
                'type': 'escalation_policy_reference'
            }}
        new_service = self._pd_api('/services', method='POST',
                                   data={'service': service_params})

        if new_service:
            service_id = new_service['service']['id']
            logger.debug('Created service "%s" (%s).', service_name, service_id)
            return service_id
        return None

    def _pd_api(self, url, data=None, method='GET'):
        url = '%s/%s' % (PD_API_BASE, url)
        request_args = {
            'headers': dict(self._pd_headers)
        }
        if six.PY3:
            request_args['method'] = method

        if data is not None:
            request_args['data'] = json.dumps(data).encode('utf-8')
            request_args['headers']['Content-Type'] = APPLICATION_JSON

        request = Request(url, **request_args)
        if six.PY2:  # pragma: no cover
            request.get_method = lambda: method

        try:
            response = urlopen(request)
            return json.loads(response.read().decode('utf-8'))
        except HTTPError as e:
            response = e.read().decode('utf-8')
            logger.warn("API error: %s", response)
            if method == 'GET' and e.code == 404:
                return None
            else:
                raise e
