import logging
from six.moves.urllib.parse import urlparse
from spacel.provision import clean_name
from spacel.provision.app.alarm.actions import ACTIONS_NONE, ACTIONS_OK_ALARM

logger = logging.getLogger('spacel.provision.app.alarm.endpoint.slack')


class SlackEndpoints(object):
    """
    Dispatches via Slack.
    Uses a Lambda function to transform SNS payload into Slack message.
    Pattern by DeviaVir.
    """

    def __init__(self, lambda_uploader):
        self._lambda_uploader = lambda_uploader

    @staticmethod
    def resource_name(name):
        return 'EndpointSlack%sTopic' % clean_name(name)

    def add_endpoints(self, template, name, params):
        url = params.get('url')
        if not url:
            logger.warning('Slack endpoint %s is missing "url".', name)
            return ACTIONS_NONE

        resources = template['Resources']

        # This may intersect with other decorators/features, that's fine.
        resources['LambdaRole'] = {
            'Type': 'AWS::IAM::Role',
            'Properties': {
                'AssumeRolePolicyDocument': {
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Principal': {
                            'Service': ['lambda.amazonaws.com']
                        },
                        'Action': ['sts:AssumeRole']
                    }]
                },
                'Path': '/',
                'Policies': [{
                    'PolicyName': 'root',
                    'PolicyDocument': {
                        'Version': '2012-10-17',
                        'Statement': [{
                            'Effect': 'Allow',
                            'Action': [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents'
                            ],
                            'Resource': 'arn:aws:logs:*:*:*'
                        }]
                    }
                }]
            }
        }

        # Upload to S3:
        slack_path = urlparse(url).path
        bucket, key = self._lambda_uploader.upload('sns-to-slack.js', {
            '__PATH__': slack_path
        })

        topic_resource = self.resource_name(name)
        resource_base = clean_name(name)
        function_resource = 'EndpointSlack%sFunction' % resource_base
        resources[function_resource] = {
            'Type': 'AWS::Lambda::Function',
            'Properties': {
                'Handler': 'index.handler',
                'Role': {'Fn::GetAtt': ['LambdaRole', 'Arn']},
                'Timeout': '3',
                'Code': {
                    'S3Bucket': bucket,
                    'S3Key': key
                },
                'Runtime': 'nodejs'
            }
        }
        resources['EndpointSlack%sPermission' % resource_base] = {
            'Type': 'AWS::Lambda::Permission',
            'DependsOn': function_resource,
            'Properties': {
                'FunctionName': {
                    'Fn::GetAtt': [
                        function_resource, 'Arn'
                    ]
                },
                'Action': 'lambda:InvokeFunction',
                'Principal': 'sns.amazonaws.com',
                'SourceArn': {'Ref': topic_resource}
            }
        }

        resources[topic_resource] = {
            'Type': 'AWS::SNS::Topic',
            'Properties': {
                'Subscription': [{
                    'Endpoint': {
                        'Fn::GetAtt': [
                            function_resource, 'Arn'
                        ]
                    },
                    'Protocol': 'lambda'
                }],
                'DisplayName': {'Fn::Join': [
                    ' ', [
                        {'Ref': 'AWS::StackName'},
                        'CloudWatchSlackAlarms']
                ]}
            }
        }
        return ACTIONS_OK_ALARM
