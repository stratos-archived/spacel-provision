from spacel.provision import clean_name
from spacel.provision.app.base_decorator import BaseTemplateDecorator
from spacel.provision.app.cloudwatch_logs_alarm import \
    CloudWatchLogsTriggerFactory


class CloudWatchLogsDecorator(BaseTemplateDecorator):
    def logs(self, app_region, resources):
        docker_logs = app_region.logging.get('docker')
        if not docker_logs:
            return

        log_group_resource = self._log_group_resource(resources, docker_logs)
        self._iam_resource(resources, log_group_resource)
        self._log_user_data(resources, log_group_resource)

        self._metrics(app_region, resources, log_group_resource)

    @staticmethod
    def _log_group_resource(resources, docker_logs):
        docker_log_retention = docker_logs.get('retention', 14)
        log_group_resource = 'DockerLogGroup'
        resources[log_group_resource] = {
            'Type': 'AWS::Logs::LogGroup',
            'Properties': {
                'RetentionInDays': docker_log_retention
            }
        }
        return log_group_resource

    @staticmethod
    def _iam_resource(resources, log_group_resource):
        log_resources = (resources['WriteLogsPolicy']
                         ['Properties']
                         ['PolicyDocument']
                         ['Statement'][0]
                         ['Resource'])
        log_resources.append({'Fn::GetAtt': [log_group_resource, 'Arn']})

    def _log_user_data(self, resources, log_group_resource):
        user_data = self._lc_user_data(resources)
        logging_intro = user_data.index('"logging":{') + 1
        user_data.insert(logging_intro, '\"},')
        user_data.insert(logging_intro, {'Ref': log_group_resource})
        user_data.insert(logging_intro, '"group":\"')
        user_data.insert(logging_intro, '"docker":{')

    def _metrics(self, app_region, resources, log_group_resource):
        metrics = app_region.logging['docker'].get('metrics', {})
        app = app_region.app
        metric_namespace = 'LogMetrics/%s/%s' % (app.name, app.orbit.name)
        trigger_factory = CloudWatchLogsTriggerFactory(metric_namespace)
        for metric_name, log_metric in metrics.items():
            self._metric(resources, log_group_resource, metric_namespace,
                         metric_name, log_metric)
            metric_alarms = log_metric.get('alarms', {})
            trigger_factory.add_cloudwatch_alarm(app_region, resources,
                                                 metric_name, metric_alarms)

    @staticmethod
    def _metric(resources, log_group_resource, metric_namespace,
                metric_name, log_metric):
        patterns = log_metric.get('patterns', {})
        for pattern, value in patterns.items():
            pattern_name = clean_name(pattern.replace('=', 'EQ')
                                      .replace('!', 'NOT')
                                      .replace('*', 'STAR'))
            resource_name = '%sMetricFilter%s' % (clean_name(metric_name),
                                                  pattern_name)
            resources[resource_name] = {
                'Type': 'AWS::Logs::MetricFilter',
                'Properties': {
                    'LogGroupName': {'Ref': log_group_resource},
                    'FilterPattern': pattern,
                    'MetricTransformations': [{
                        'MetricValue': value,
                        'MetricName': metric_name,
                        'MetricNamespace': metric_namespace
                    }]
                }
            }
