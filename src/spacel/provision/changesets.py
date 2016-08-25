import logging

logger = logging.getLogger('spacel')

# These could always use tuning:
COSTS = {
    'AWS::AutoScaling::AutoScalingGroup': {
        'Add': 2,
        'Modify': 300,
        'Delete': 2
    },
    'AWS::AutoScaling::LaunchConfiguration': {
        'Add': 2,
        'Modify': 2,
        'Delete': 2
    },
    'AWS::CloudWatch::Alarm': {
        'Add': 15,
        'Modify': 15,
        'Delete': 15
    },
    'AWS::DynamoDB::Table': {
        'Add': 30,
        'Modify': 5,
        'Delete': 30
    },
    'AWS::EC2::EIP': {
        'Add': 15,
        'Modify': 5,
        'Delete': 15
    },
    'AWS::EC2::NatGateway': {
        'Add': 60,
        'Delete': 60
    },
    'AWS::EC2::Route': {
        'Add': 5,
        'Modify': 5,
        'Delete': 5
    },
    'AWS::EC2::RouteTable': {
        'Add': 5,
        'Modify': 5,
        'Delete': 5
    },
    'AWS::EC2::SecurityGroup': {
        'Add': 140,
        'Modify': 2,
        'Delete': 5
    },
    'AWS::EC2::SubnetRouteTableAssociation': {
        'Add': 5,
        'Delete': 5
    },
    'AWS::EC2::Subnet': {
        'Add': 5,
        'Delete': 5
    },
    'AWS::IAM::Role': {
        'Add': 75,
        'Modify': 60,
        'Delete': 75
    },
    'AWS::IAM::InstanceProfile': {
        'Add': 120,
        'Modify': 60,
        'Delete': 120
    }
}


class ChangeSetEstimator(object):
    """
    Estimate how long it will take to execute a CF change set.
    """

    def estimate(self, changes):
        # Aggregate changes in a single log message:
        changes_debug = 'Changes to be performed:\n'
        seconds = 0

        for change in changes:
            resource_change = change.get('ResourceChange')
            if resource_change:
                physical = resource_change.get('PhysicalResourceId')
                if physical:
                    physical = ' (%s)' % physical
                else:
                    physical = ''
                resource_action = resource_change['Action']
                resource_type = resource_change['ResourceType']

                # Debug message:
                changes_debug += '%6s %25s - %s%s\n' % (
                    resource_action,
                    resource_type,
                    resource_change['LogicalResourceId'],
                    physical)

                seconds += self._estimate(resource_action, resource_type)

        changes_debug += 'This should take %s seconds...' % seconds
        logger.info(changes_debug)
        return seconds

    @staticmethod
    def _estimate(resource_action, resource_type):
        basic_cost = COSTS.get(resource_type, {}).get(resource_action)
        if basic_cost:
            return basic_cost

        logger.warn('No basic cost for %s to %s.', resource_action,
                    resource_type)
        return 0
