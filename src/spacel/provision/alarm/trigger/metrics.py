import logging

logger = logging.getLogger('')


class MetricDefinitions(object):
    def __init__(self):
        self._metrics = {}
        self._ec2_metrics()
        self._elb_metrics()
        self._system_metrics()

        logger.debug('Loaded %d metric definitions.', len(self._metrics))

    def _ec2_metrics(self):
        """
        http://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ec2-metricscollected.html
        :return:
        """
        asg_dimensions = [{
            'Name': 'AutoScalingGroupName',
            'Value': {'Ref': 'Asg'}
        }]
        self._metric([
            'EC2/CPUCreditUsage'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'CPUCreditUsage',
            'statistic': 'Maximum',
            'threshold': '>5',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/CPUCreditBalance',
            'cpucredits'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'CPUCreditBalance',
            'statistic': 'Minimum',
            'threshold': '<1',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/CPUUtilization',
            'CPU'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'CPUUtilization',
            'statistic': 'Average',
            'threshold': '>85',
            'period': '10x60',
            'dimensions': asg_dimensions
        })

        self._metric([
            'EC2/DiskReadOps'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'DiskReadOps',
            'statistic': 'Maximum',
            'threshold': '>200',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/DiskWriteOps'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'DiskWriteOps',
            'statistic': 'Maximum',
            'threshold': '>200',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/DiskReadBytes'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'DiskReadBytes',
            'statistic': 'Maximum',
            'threshold': '>20971520',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/DiskWriteBytes'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'DiskWriteBytes',
            'statistic': 'Maximum',
            'threshold': '>20971520',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/NetworkIn'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'NetworkIn',
            'statistic': 'Maximum',
            'threshold': '>20971520',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/NetworkOut'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'NetworkOut',
            'statistic': 'Average',
            'threshold': '>20971520',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/NetworkPacketsIn'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'NetworkPacketsIn',
            'statistic': 'Average',
            'threshold': '>1000',
            'period': '3x60',
            'dimensions': asg_dimensions
        })
        self._metric([
            'EC2/NetworkPacketsOut'
        ], {
            'namespace': 'AWS/EC2',
            'metricName': 'NetworkPacketsOut',
            'statistic': 'Average',
            'threshold': '>1000',
            'period': '3x60',
            'dimensions': asg_dimensions
        })

    def _elb_metrics(self):
        """
        http://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/elb-metricscollected.html
        :return:
        """
        elb_dimensions = [{
            'Name': 'LoadBalancerName',
            'Value': {
                'Fn::If': [
                    'ElbPublic',
                    {'Ref': 'PublicElb'},
                    {'Ref': 'PrivateElb'}
                ]
            }
        }]
        self._metric([
            'ELB/UnHealthyHostCount',
            'unhealthyhosts',
            'unhealthy'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'UnHealthyHostCount',
            'statistic': 'Average',
            'threshold': '>1',
            'period': '3x60',
            'dimensions': elb_dimensions
        })
        self._metric([
            'ELB/HealthyHostCount',
            'healthyhosts',
            'healthy'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'HealthyHostCount',
            'statistic': 'Average',
            'threshold': '<=0',
            'period': '3x60',
            'dimensions': elb_dimensions
        })
        self._metric([
            'ELB/BackendConnectionErrors',
            'connectionerrors'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'BackendConnectionErrors',
            'statistic': 'Sum',
            'threshold': '>10',
            'period': '3x60',
            'dimensions': elb_dimensions
        })
        self._metric([
            'ELB/Latency'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'Latency',
            'statistic': 'Average',
            'threshold': '>10',
            'period': '3x60',
            'dimensions': elb_dimensions
        })

        self._metric([
            'ELB/RequestCount',
            'requests'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'RequestCount',
            'statistic': 'Sum',
            'threshold': '<1',
            'period': '3x60',
            'dimensions': elb_dimensions
        })

        self._metric([
            'ELB/SpilloverCount',
            'spillover'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'SpilloverCount',
            'statistic': 'Sum',
            'threshold': '>0',
            'period': '3x60',
            'dimensions': elb_dimensions
        })

        self._metric([
            'ELB/SurgeQueueLength',
            'surgequeue'
        ], {
            'namespace': 'AWS/ELB',
            'metricName': 'SurgeQueueLength',
            'statistic': 'Max',
            'threshold': '>0',
            'period': '3x60',
            'dimensions': elb_dimensions
        })

        for backend_status in range(2, 6):
            self._metric([
                'ELB/HTTPCode_Backend_%sXX' % backend_status,
                'backend%sXX' % backend_status
            ], {
                'namespace': 'AWS/ELB',
                'metricName': 'HTTPCode_Backend_%sXX' % backend_status,
                'statistic': 'Sum',
                'threshold': '>10',
                'period': '3x60',
                'dimensions': elb_dimensions
            })

        for elb_status in range(4, 6):
            self._metric([
                'ELB/HTTPCode_ELB_%sXX' % elb_status,
                'elb%sXX' % elb_status,
                'status%sXX' % elb_status
            ], {
                'namespace': 'AWS/ELB',
                'metricName': 'HTTPCode_ELB_%sXX' % elb_status,
                'statistic': 'Sum',
                'threshold': '>10',
                'period': '3x60',
                'dimensions': elb_dimensions
            })

    def _system_metrics(self):
        self._metric([
            'System/DiskSpaceUtilization',
            'disk'
        ], {
            'namespace': 'System/Linux',
            'metricName': 'DiskSpaceUtilization',
            'statistic': 'Average',
            'threshold': '>85',
            'period': '10x60',
            'dimensions': [{
                'Name': 'AutoScalingGroupName',
                'Value': {'Ref': 'Asg'}
            }, {
                'Name': 'Filesystem',
                'Value': '-'
            }, {
                'Name': 'MountPath',
                'Value': '/'
            }]
        })
        self._metric([
            'System/MemoryUtilization',
            'memory',
            'ram'
        ], {
            'namespace': 'System/Linux',
            'metricName': 'MemoryUtilization',
            'statistic': 'Average',
            'threshold': '>85',
            'period': '10x60',
            'dimensions': [{
                'Name': 'AutoScalingGroupName',
                'Value': {'Ref': 'Asg'}
            }]
        })

    def _metric(self, aliases, data):
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower in self._metrics:  # pragma: no cover
                logger.warn('Duplicate metric: %s', alias)
                continue
            self._metrics[alias_lower] = data

            alias_split = alias_lower.split('/', 2)
            if len(alias_split) == 2:
                self._metrics[alias_split[1]] = data

    def get(self, name):
        # TODO: special names can mutate dimensions? i.e. 'disk@/mnt/foo'
        return self._metrics.get(name.lower())
