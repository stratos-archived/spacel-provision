import datetime
import json
import logging
import re
import time
import uuid
from collections import defaultdict

from botocore.exceptions import ClientError

logger = logging.getLogger('spacel.provision.cloudformation')

CAPABILITIES = ('CAPABILITY_IAM',)
INVALID_STATE_MESSAGE = re.compile('.* is in ([A-Z_]*) state and can not'
                                   ' be updated.')

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
MAX_TEMPLATE_BODY_SIZE = 51200

NO_CHANGES = 'The submitted information didn\'t contain changes.' \
             ' Submit different information to create a change set.'

CF_STACK = 'AWS::CloudFormation::Stack'
FINAL_STATUS = ('CREATE_COMPLETE', 'DELETE_COMPLETE', 'UPDATE_COMPLETE',
                'UPDATE_ROLLBACK_COMPLETE')
ROLLBACK_STATUS = ('UPDATE_ROLLBACK_COMPLETE', 'ROLLBACK_COMPLETE',
                   'UPDATE_ROLLBACK_FAILED')


class BaseCloudFormationFactory(object):
    """
    Shared functionality for CloudFormation provisioning.
    """

    def __init__(self, clients, change_sets, uploader, sleep_time=2):
        self._clients = clients
        self._change_sets = change_sets
        self._sleep_time = sleep_time
        self._uploader = uploader

    def _stack(self, name, region, json_template, parameters=None,
               secret_parameters=None):
        parameters = parameters or {}
        secret_parameters = secret_parameters or {}
        cf = self._clients.cloudformation(region)
        template_body = json.dumps(json_template, indent=2, sort_keys=True)
        if len(template_body) >= MAX_TEMPLATE_BODY_SIZE:
            template_url = self._uploader.upload(template_body, name)
        else:
            template_url = None
        parameters = [{'ParameterKey': k, 'ParameterValue': v}
                      for k, v in parameters.items()]

        if secret_parameters:
            existing_params = self._existing_params(cf, name)
            for secret_param, value_func in secret_parameters.items():
                if secret_param in existing_params:
                    # Param exists in CloudFormation, re-use previous value:
                    parameters.append({
                        'ParameterKey': secret_param,
                        'UsePreviousValue': True
                    })
                else:
                    # Parameter does not exist, generate a fresh value/lookup:
                    secret_value = value_func()
                    parameters.append({
                        'ParameterKey': secret_param,
                        'ParameterValue': secret_value
                    })

        set_name = 'change-%s' % uuid.uuid4()
        try:
            logger.debug('Updating stack %s in %s.', name, region)
            create_params = {
                'StackName': name,
                'ChangeSetName': set_name,
                'Parameters': parameters,
                'Capabilities': CAPABILITIES
            }
            if template_url:
                create_params['TemplateURL'] = template_url
            else:
                create_params['TemplateBody'] = template_body
            cf.create_change_set(**create_params)

            # Wait for change set to complete:
            change_set = cf.describe_change_set(StackName=name,
                                                ChangeSetName=set_name)
            while change_set['Status'] != 'CREATE_COMPLETE':
                if change_set['Status'] == 'FAILED':
                    status_reason = change_set.get('StatusReason')

                    if status_reason == NO_CHANGES:
                        logger.debug('No changes to be performed.')
                        cf.delete_change_set(StackName=name,
                                             ChangeSetName=set_name)
                        return None
                    else:
                        logger.error('Unable to create change set "%s": %s',
                                     set_name, status_reason)
                        return 'failed'

                time.sleep(self._sleep_time)
                change_set = cf.describe_change_set(StackName=name,
                                                    ChangeSetName=set_name)

            # Debug info before executing:
            self._change_sets.estimate(change_set['Changes'])

            # Start execution:
            cf.execute_change_set(StackName=name,
                                  ChangeSetName=set_name)
            cf.delete_change_set(StackName=name,
                                 ChangeSetName=set_name)
            return 'update'
        except ClientError as e:
            e_message = e.response['Error'].get('Message')

            not_exist = e_message == ('Stack [%s] does not exist' % name)
            if not_exist:
                logger.debug('Stack %s not found in %s, creating.', name,
                             region)

                create_params = {
                    'StackName': name,
                    'Parameters': parameters,
                    'Capabilities': CAPABILITIES
                }
                if template_url:
                    create_params['TemplateURL'] = template_url
                else:
                    create_params['TemplateBody'] = template_body
                cf.create_stack(**create_params)
                return 'create'

            state_match = INVALID_STATE_MESSAGE.match(e_message)
            if state_match:
                current_state = state_match.group(1)

                waiter = None
                if current_state.startswith('CREATE_'):
                    waiter = cf.get_waiter('stack_create_complete')
                elif current_state.startswith('UPDATE_'):
                    waiter = cf.get_waiter('stack_update_complete')
                elif current_state == 'ROLLBACK_COMPLETE':
                    cf.delete_stack(StackName=name)
                    waiter = cf.get_waiter('stack_delete_complete')
                else:  # pragma: no cover
                    logger.warning('Unknown state: %s', current_state)

                if waiter:
                    logger.debug('Stack %s is %s, waiting...', name,
                                 current_state)
                    self._impatient(waiter)
                    waiter.wait(StackName=name)
                    return self._stack(name, region, json_template)
            raise e

    @staticmethod
    def _existing_params(cf, name):
        try:
            stack = cf.describe_stacks(StackName=name)
            existing_parameters = [param['ParameterKey']
                                   for param in (stack['Stacks'][0]
                                                 ['Parameters'])]
        except ClientError:
            existing_parameters = []
        return set(existing_parameters)

    def _delete_stack(self, name, region):
        cf = self._clients.cloudformation(region)
        cf.delete_stack(StackName=name)
        return 'delete'

    @staticmethod
    def _describe_stack(cf, stack_name):
        return cf.describe_stacks(StackName=stack_name)['Stacks'][0]

    def _wait_for_updates(self, name, updates, poll_interval=5):
        """
        Wait for updates to complete in a stack.
        :param name: Application name.
        :param updates: Stack update dict of {region:update}.
        :param poll_interval: Interval to poll for updates/completion.
        :return: True if updates completed.
        """
        start_offset = datetime.timedelta(seconds=5)
        start = datetime.datetime.utcnow() - start_offset

        # Collect regions that require updates:
        pending = {}
        for region, update in updates.items():
            if not update:
                continue
            if update == 'failed':
                logger.debug('Update failed for %s in %s...', name, region)
                continue
            pending[region] = start

        if not pending:
            return True

        resource_starts = defaultdict(dict)
        resource_times = defaultdict(dict)

        # Loop until every region is finished:
        rollback_count = 0
        while pending:
            for region, last_log in pending.copy().items():
                # Get stack events in this region
                cf = self._clients.cloudformation(region)
                try:
                    events = (cf.describe_stack_events(StackName=name)
                              .get('StackEvents', ()))
                except ClientError as e:
                    # Deleting a stack that doesn't exist is fine:
                    if updates[region] == 'delete':
                        e_message = e.response['Error'].get('Message')
                        if 'does not exist' in e_message:
                            del pending[region]
                            continue
                    raise e

                region_starts = resource_starts[region]
                region_times = resource_times[region]

                # Iterate events in chronological order:
                for event in reversed(events):
                    # Skip events that have been processed:
                    event_time = event['Timestamp'].replace(tzinfo=None)
                    if event_time <= last_log:
                        continue

                    # If this is a "stack complete" event, remove from pending:
                    resource_id = event['LogicalResourceId']
                    resource_type = event['ResourceType']
                    status = event['ResourceStatus']
                    is_stack = resource_id == name and resource_type == CF_STACK
                    is_complete = is_stack and status in FINAL_STATUS
                    if is_complete:
                        del pending[region]

                    # Track the first mention of each resource
                    # Calculate CREATE/UPDATE time for each resource:
                    if resource_id not in region_starts:
                        region_starts[resource_id] = time.time()
                    elif (status in FINAL_STATUS
                          and resource_id not in resource_starts):
                        resource_start = region_starts.get(resource_id)
                        region_times[resource_id] = time.time() - resource_start

                    is_rollback = is_stack and status in ROLLBACK_STATUS
                    if is_rollback:
                        rollback_count += 1

                    # Flush any remaining events to log:
                    status_reason = event.get('ResourceStatusReason', '')
                    if status_reason:
                        status_reason = ' (%s)' % status_reason
                    logger.debug('Resource %s - %s - %s%s at %s',
                                 region,
                                 resource_id,
                                 status,
                                 status_reason,
                                 event_time.strftime('%Y-%m-%d %H:%M:%S'))

                    # Push "start" to the last logged event
                    if not is_complete:
                        pending[region] = event_time

            # Wait before retrying each pending region again:
            if pending:
                time.sleep(poll_interval)

        if resource_times:
            times_str = json.dumps(dict(resource_times), indent=2,
                                   sort_keys=True)
            logger.debug('Resource times: %s', times_str)

        end = datetime.datetime.utcnow()
        duration = (end - start - start_offset).total_seconds()
        logger.info('Completed all updates in %i seconds, %s rollbacks.',
                    duration, rollback_count)
        return rollback_count == 0

    @staticmethod
    def _impatient(waiter):
        """
        Reduce delay on waiter.
        :param waiter: Waiter.
        """
        # Default polls every 30 seconds; 5 makes more sense to me:
        waiter.config.delay /= 6
        waiter.config.max_attempts *= 6
