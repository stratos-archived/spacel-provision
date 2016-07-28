import unittest

from spacel.provision.changesets import ChangeSetEstimator


class TestChangeSetEstimator(unittest.TestCase):
    def setUp(self):
        self._change_sets = ChangeSetEstimator()
        self.changes = [
            {
                'ResourceChange': {
                    'Action': 'Add',
                    'ResourceType': 'AWS::IAM::Role',
                    'LogicalResourceId': 'Role',
                    'PhysicalResourceId': 'test-Role-RCUJMT5J76BR'
                }
            }
        ]

    def test_estimate(self):
        estimate = self._change_sets.estimate(self.changes)
        self.assertNotEquals(0, estimate)

    def test_estimate_no_physical(self):
        del self.changes[0]['ResourceChange']['PhysicalResourceId']
        estimate = self._change_sets.estimate(self.changes)
        self.assertNotEquals(0, estimate)

    def test_estimate_not_available(self):
        self.changes[0]['ResourceChange']['ResourceType'] = 'AWS::IAM::NotReal'
        estimate = self._change_sets.estimate(self.changes)
        self.assertEquals(0, estimate)
