import logging
from spacel.provision import clean_name
from spacel.provision.alarm.actions import ACTION_ALARM, ACTIONS_NONE

logger = logging.getLogger('spacel.provision.alarm.endpoint.scale')


class ScaleEndpoints(object):
    """
    Modifies AutoScaling capacity in response to alarm.
    """

    def __init__(self, direction=None):
        self._direction = direction

    def add_endpoints(self, template, name, params):
        adjustment = params.get('adjustment', 1)

        adjustment_type = 'ChangeInCapacity'
        if isinstance(adjustment, str) and '%' in adjustment:
            adjustment_type = 'PercentChangeInCapacity'
            adjustment = int(adjustment.replace('%', ''))

        adjustment = self._calculate_adjustment(adjustment)
        if not adjustment:
            logger.warn('Scaling endpoint %s has invalid "adjustment".', name)
            return ACTIONS_NONE

        cooldown = params.get('cooldown', '300')

        resources = template['Resources']
        resource_name = self.resource_name(name)
        resources[resource_name] = {
            'Type': 'AWS::AutoScaling::ScalingPolicy',
            'Properties': {
                'AdjustmentType': adjustment_type,
                'AutoScalingGroupName': {'Ref': 'Asg'},
                'Cooldown': cooldown,
                'ScalingAdjustment': adjustment
            }
        }
        return ACTION_ALARM,

    def _calculate_adjustment(self, adjustment):
        if self._direction is not None:
            adjustment = abs(adjustment) * self._direction
        return int(adjustment)

    @staticmethod
    def resource_name(name):
        return 'EndpointScale%sPolicy' % clean_name(name)
