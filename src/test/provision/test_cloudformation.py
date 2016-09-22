from botocore.exceptions import ClientError
from mock import MagicMock, ANY
import unittest

from spacel.aws.clients import ClientCache
from spacel.provision.changesets import ChangeSetEstimator
from spacel.provision.cloudformation import (BaseCloudFormationFactory,
                                             NO_CHANGES)
from spacel.provision.s3.template_uploader import TemplateUploader

NAME = 'test-stack'
REGION = 'us-east-1'
TEMPLATE = {}
NO_CHANGE_SET = {'Status': 'FAILED', 'StatusReason': NO_CHANGES}


class TestBaseCloudFormationFactory(unittest.TestCase):
    def setUp(self):
        self.cloudformation = MagicMock()
        self.clients = MagicMock(spec=ClientCache)
        self.clients.cloudformation.return_value = self.cloudformation
        self.change_sets = MagicMock(spec=ChangeSetEstimator)
        self.templates = MagicMock(spec=TemplateUploader)

        self.cf_factory = BaseCloudFormationFactory(self.clients,
                                                    self.change_sets,
                                                    self.templates,
                                                    sleep_time=0.00001)

    def test_stack_not_found(self):
        not_found = ClientError({'Error': {
            'Message': 'Stack [test-stack] does not exist'
        }}, 'CreateChangeSet')
        self.cloudformation.create_change_set.side_effect = not_found

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.assertEqual(result, 'create')
        self.cloudformation.create_stack.assert_called_with(
            StackName=NAME,
            Parameters=ANY,
            TemplateURL=ANY,
            Capabilities=ANY
        )
        self.change_sets.estimate.assert_not_called()

    def test_stack_no_changes(self):
        self.cloudformation.describe_change_set.return_value = NO_CHANGE_SET

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.assertIsNone(result)
        self.change_sets.estimate.assert_not_called()

    def test_stack_change_set_failed(self):
        self.cloudformation.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': 'Kaboom'
        }

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.assertEqual(result, 'failed')
        self.change_sets.estimate.assert_not_called()

    def test_stack_change_set_success(self):
        self.cloudformation.describe_change_set.side_effect = [
            {'Status': 'CREATE_IN_PROGRESS'},
            {'Status': 'CREATE_COMPLETE', 'Changes': []}
        ]

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.change_sets.estimate.assert_called_with(ANY)
        self.assertEqual(result, 'update')

    def test_stack_create_in_progress(self):
        create_in_progress = ClientError({'Error': {
            'Message': self._in_progress('CREATE_IN_PROGRESS')
        }}, 'CreateChangeSet')
        self.cloudformation.create_change_set.side_effect = [
            create_in_progress,
            None
        ]
        self.cloudformation.describe_change_set.return_value = NO_CHANGE_SET

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.assertIsNone(result)
        self.cloudformation.get_waiter.assert_called_with(
            'stack_create_complete')

    def test_stack_update_in_progress(self):
        update_in_progress = ClientError({'Error': {
            'Message': self._in_progress('UPDATE_IN_PROGRESS')
        }}, 'CreateChangeSet')
        self.cloudformation.create_change_set.side_effect = [
            update_in_progress,
            None
        ]
        self.cloudformation.describe_change_set.return_value = NO_CHANGE_SET

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.assertIsNone(result)
        self.cloudformation.get_waiter.assert_called_with(
            'stack_update_complete')

    def test_stack_exception(self):
        client_error = ClientError({'Error': {
            'Message': 'Kaboom'
        }}, 'CreateChangeSet')

        self.cloudformation.create_change_set.side_effect = client_error

        self.assertRaises(ClientError, self.cf_factory._stack, NAME, REGION,
                          TEMPLATE)

    def test_stack_rollback_complete(self):
        rollback_complete = ClientError({'Error': {
            'Message': self._in_progress('ROLLBACK_COMPLETE')
        }}, 'CreateChangeSet')
        self.cloudformation.create_change_set.side_effect = [
            rollback_complete,
            None
        ]
        self.cloudformation.describe_change_set.return_value = NO_CHANGE_SET

        result = self.cf_factory._stack(NAME, REGION, TEMPLATE)

        self.assertIsNone(result)
        self.cloudformation.get_waiter.assert_called_with(
            'stack_delete_complete')

    def test_stack_secret_param_generated(self):
        self.cloudformation.describe_change_set.side_effect = [
            {'Status': 'CREATE_COMPLETE', 'Changes': []}
        ]

        secret_func = MagicMock()
        self.cf_factory._stack(NAME, REGION, TEMPLATE,
                               secret_parameters={
                                   'TopSecret': secret_func
                               })
        secret_func.assert_called_once()

    def test_stack_secret_param_reused(self):
        self.cloudformation.describe_stacks.return_value = {
            'Stacks': [
                {'Parameters': [
                    {'ParameterKey': 'TopSecret'}
                ]}
            ]
        }
        self.cloudformation.describe_change_set.return_value = \
            {'Status': 'CREATE_COMPLETE', 'Changes': []}

        secret_func = MagicMock()
        self.cf_factory._stack(NAME, REGION, TEMPLATE,
                               secret_parameters={
                                   'TopSecret': secret_func
                               })
        secret_func.assert_not_called()

    def test_existing_params_error(self):
        self.cloudformation.describe_stacks.side_effect = ClientError({'Error': {
            'Message': 'Stack [test-stack] does not exist'
        }}, 'DescribeStack')

        params = self.cf_factory._existing_params(self.cloudformation, NAME)
        self.assertEquals(0, len(params))

    def test_delete_stack(self):
        self.cf_factory._delete_stack(NAME, REGION)
        self.cloudformation.delete_stack.assert_called_with(StackName=NAME)

    def test_wait_for_updates_skip_noops(self):
        self.cf_factory._wait_for_updates(NAME, {
            REGION: None
        })

        self.cloudformation.get_waiter.assert_not_called()

    def test_wait_for_updates_skip_failed(self):
        self.cf_factory._wait_for_updates(NAME, {
            REGION: 'failed'
        })

        self.cloudformation.get_waiter.assert_not_called()

    def test_wait_for_updates(self):
        self.cf_factory._wait_for_updates(NAME, {
            REGION: 'update'
        })

        self.cloudformation.get_waiter.assert_called_with(
            'stack_update_complete')

    @staticmethod
    def _in_progress(state):
        return 'test-stack is in %s state and can not be updated.' % state
