from spacel.provision.app.base_decorator import BaseTemplateDecorator


class CloudWatchLogsDecorator(BaseTemplateDecorator):
    def logs(self, app_region, resources):
        docker_logs = app_region.logging.get('docker')
        if not docker_logs:
            return

        # Add LogGroup resource:
        docker_log_retention = docker_logs.get('retention', 14)
        log_group_resource = 'DockerLogGroup'
        resources[log_group_resource] = {
            'Type': 'AWS::Logs::LogGroup',
            'Properties': {
                'RetentionInDays': docker_log_retention
            }
        }

        # Add IAM permission:
        log_resources = (resources['WriteLogsPolicy']
                         ['Properties']
                         ['PolicyDocument']
                         ['Statement'][0]
                         ['Resource'])
        log_resources.append({'Fn::GetAtt': [log_group_resource, 'Arn']})

        # Add to UserData:
        user_data = self._user_data(resources)
        logging_intro = user_data.index('"logging":{') + 1
        user_data.insert(logging_intro, '\"},')
        user_data.insert(logging_intro, {'Ref': log_group_resource})
        user_data.insert(logging_intro, '"group":\"')
        user_data.insert(logging_intro, '"docker":{')
