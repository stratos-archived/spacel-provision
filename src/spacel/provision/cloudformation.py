from botocore.exceptions import ClientError
import json
import logging
import re

logger = logging.getLogger('')

CAPABILITIES = ('CAPABILITY_IAM',)
INVALID_STATE_MESSAGE = re.compile('.* is in ([A-Z_]*) state and can not'
                                   ' be updated.')


def key_sorted(some_dict):
    return [value for (key, value) in sorted(some_dict.items())]


class BaseCloudFormationFactory(object):
    """
    Shared functionality for CloudFormation provisioning.
    """

    def __init__(self, clients):
        self._clients = clients

    def _stack(self, name, region, json_template):
        cf = self._clients.cloudformation(region)
        template = json.dumps(json_template, indent=2)

        try:
            logger.debug('Updating stack %s in %s.', name, region)
            cf.update_stack(
                StackName=name,
                TemplateBody=template,
                Capabilities=CAPABILITIES
            )
            return 'update'
        except ClientError as e:
            e_message = e.response['Error'].get('Message')

            not_exist = e_message == ('Stack [%s] does not exist' % name)
            if not_exist:
                logger.debug('Stack %s not found in %s, creating.', name,
                             region)
                cf.create_stack(
                    StackName=name,
                    TemplateBody=template,
                    Capabilities=CAPABILITIES
                )
                return 'create'

            no_changes = e_message == 'No updates are to be performed.'
            if no_changes:
                logger.debug('No changes to be performed.')
                return None

            state_match = INVALID_STATE_MESSAGE.match(e_message)
            if state_match:
                current_state = state_match.group(1)

                waiter = None
                if current_state.startswith('CREATE_'):
                    waiter = cf.get_waiter('stack_create_complete')
                elif current_state.startswith('UPDATE_'):
                    waiter = cf.get_waiter('stack_update_complete')
                else:
                    logger.warn('Unknown state: %s', current_state)

                if waiter:
                    logger.debug('Stack %s is %s, waiting...', name,
                                 current_state)
                    self._impatient(waiter)
                    waiter.wait(StackName=name)
                    return self._stack(name, region, json_template)
            raise e

    @staticmethod
    def _describe_stack(cf, stack_name):
        return cf.describe_stacks(StackName=stack_name)['Stacks'][0]

    def _wait_for_updates(self, name, updates):
        for region, update in updates.items():
            if not update:
                continue

            cf = self._clients.cloudformation(region)
            logger.debug('Waiting for %s in %s...', name, region)
            waiter = cf.get_waiter('stack_%s_complete' % update)
            self._impatient(waiter)
            waiter.wait(StackName=name)

    @staticmethod
    def _impatient(waiter):
        """
        Reduce delay on waiter.
        :param waiter: Waiter.
        """
        # Default polls every 30 seconds; 5 makes more sense to me:
        waiter.config.delay /= 6
        waiter.config.max_attempts *= 6
