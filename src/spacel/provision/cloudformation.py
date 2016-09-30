import logging
import re
import time
import uuid

from botocore.exceptions import ClientError

logger = logging.getLogger('spacel.provision.cloudformation')

CAPABILITIES = ('CAPABILITY_IAM',)
INVALID_STATE_MESSAGE = re.compile('.* is in ([A-Z_]*) state and can not'
                                   ' be updated.')

NO_CHANGES = 'The submitted information didn\'t contain changes.' \
             ' Submit different information to create a change set.'


def key_sorted(some_dict):
    return [value for (key, value) in sorted(some_dict.items())]


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
        template_url = self._uploader.upload(json_template, name)
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
            cf.create_change_set(StackName=name,
                                 ChangeSetName=set_name,
                                 Parameters=parameters,
                                 TemplateURL=template_url,
                                 Capabilities=CAPABILITIES)

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
                cf.create_stack(
                    StackName=name,
                    Parameters=parameters,
                    TemplateURL=template_url,
                    Capabilities=CAPABILITIES
                )
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

    def _wait_for_updates(self, name, updates):
        start = time.time()
        waited = False
        for region, update in updates.items():
            if not update:
                continue
            if update == 'failed':
                logger.debug('Update failed for %s in %s...', name, region)
                continue
            waited = True

            cf = self._clients.cloudformation(region)
            logger.debug('Waiting for %s in %s...', name, region)
            waiter = cf.get_waiter('stack_%s_complete' % update)
            self._impatient(waiter)
            waiter.wait(StackName=name)
            logger.debug('Completed %s in %s.', name, region)

        if waited:
            logger.info('Completed all updates in %i seconds.',
                        time.time() - start)

    @staticmethod
    def _impatient(waiter):
        """
        Reduce delay on waiter.
        :param waiter: Waiter.
        """
        # Default polls every 30 seconds; 5 makes more sense to me:
        waiter.config.delay /= 6
        waiter.config.max_attempts *= 6
