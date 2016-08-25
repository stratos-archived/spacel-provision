import logging
from urllib.parse import urlparse
from spacel.provision.alarm.alert import clean_name

logger = logging.getLogger('spacel.provision.alarms.alerts.slack')


class SlackAlerts(object):
    """
    Dispatches alert via Slack.
    Uses a Lambda function to transform SNS alert into Slack message.
    Pattern by DeviaVir.
    """

    def __init__(self, lambda_uploader):
        self._lambda_uploader = lambda_uploader

    @staticmethod
    def resource_name(name):
        return 'AlertSlack%sTopic' % clean_name(name)

    def add_alerts(self, template, name, params):
        url = params.get('url')
        if not url:
            logger.warn('Slack alert %s is missing "url".', name)
            return False

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

        slack_path = urlparse(url).path
        bucket, key = self._lambda_uploader.upload('sns-to-slack.js', {
            '__PATH__': slack_path
        })

        # TODO: upload code to S3
        topic_resource = self.resource_name(name)

        resource_base = clean_name(name)
        function_resource = 'AlertSlack%sFunction' % resource_base
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
        resources['AlertSlack%sPermission' % resource_base] = {
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
                        'CloudWatchEmailAlarms']
                ]}
            }
        }
        return True
