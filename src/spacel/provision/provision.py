import boto3
from botocore.exceptions import ClientError
import json
import logging
import re

from spacel.aws import ClientCache
from spacel.provision.templates import TemplateCache

logger = logging.getLogger('orbit')

CAPABILITIES = ('CAPABILITY_IAM',)
INVALID_STATE_MESSAGE = re.compile('.* is in ([A-Z_]*) state and can not'
                                   ' be updated.')


class CloudProvisioner(object):
    def __init__(self):
        self._templates = TemplateCache()
        self._clients = ClientCache()

    def orbit(self, orbit):
        self._azs(orbit)
        self._orbit_stack(orbit, 'vpc')
        self._orbit_stack(orbit, 'tables')
        self._orbit_stack(orbit, 'bastion')

        for region in orbit.regions:
            bastion_eips = sorted(orbit.bastion_eips(region).values())
            logger.debug('Bastions: %s - %s', region, ' '.join(bastion_eips))

    def app(self, app):
        app_name = app.full_name
        updates = {}
        for region in app.regions:
            template = self._templates.app(app, region)
            updated = self._stack(app_name, region, template)
            if updated:
                updates[region] = updated

        self._wait_for_updates(app_name, updates)

    def _orbit_stack(self, orbit, stack_suffix):
        stack_name = '%s-%s' % (orbit.name, stack_suffix)

        updates = {}
        for region in orbit.regions:
            logger.debug('Provisioning %s in %s.', stack_name, region)
            template = self._templates.for_orbit(stack_suffix, orbit, region)
            updated = self._stack(stack_name, region, template)
            if updated:
                updates[region] = updated

        if updates:
            logger.debug('Requested %s in %s, waiting for provisioning...',
                         stack_name, region)
            self._wait_for_updates(stack_name, updates)
        logger.debug('Provisioned %s in %s.', stack_name, region)

        # Refresh model from CF:
        for region in orbit.regions:
            cf = self._clients.cloudformation(region)
            cf_stack = self._describe_stack(cf, stack_name)
            cf_outputs = cf_stack.get('Outputs', {})
            orbit.update_from_cf(stack_suffix, region, cf_outputs)

    def _wait_for_updates(self, name, updates):
        for region, update in updates.items():
            if not update:
                continue

            cf = self._clients.cloudformation(region)
            logger.debug('Waiting for %s in %s...', name, region)
            waiter = cf.get_waiter('stack_%s_complete' % update)
            self._impatient(waiter)
            waiter.wait(StackName=name)

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

    def _azs(self, orbit):
        for region in orbit.regions:
            ec2 = self._clients.ec2(region)
            try:
                vpcs = ec2.describe_vpcs()
                vpc_id = vpcs['Vpcs'][0]['VpcId']
                invalid_az = region + '-zzz'
                ec2.create_subnet(VpcId=vpc_id, CidrBlock='172.31.192.0/20',
                                  AvailabilityZone=invalid_az)
            except ClientError as e:
                message = e.response['Error'].get('Message')
                if not message or 'Subnets can currently only be created in ' \
                                  'the following availability zones' not in message:
                    raise e
            message_split = message.split(region)
            # Invalid region is echoed back, every mention after that is an AZ:
            azs = sorted([region + s[0] for s in message_split[2:]])
            orbit.set_azs(region, azs)

    @staticmethod
    def _impatient(waiter):
        """
        Reduce delay on waiter.
        :param waiter: Waiter.
        """
        # Default polls every 30 seconds; 5 makes more sense to me:
        waiter.config.delay /= 6
        waiter.config.max_attempts *= 6
