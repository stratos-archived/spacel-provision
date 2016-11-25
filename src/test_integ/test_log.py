import time
import uuid

from test_integ import BaseIntegrationTest, ORBIT_REGION


class TestLogging(BaseIntegrationTest):
    def setUp(self):
        super(TestLogging, self).setUp()
        self._app_eip_only()
        self.start = int(time.time() * 1000) - 5000

    def test_01_deploy_logging(self):
        """Re-deploy application, verify spacel-agent logs are published."""
        random_message = str(uuid.uuid4())
        for app_region in self.app.regions.values():
            app_region.services['laika'].environment = {
                'MESSAGE': random_message
            }
        self.provision()

        logs = self._get_logs('DeployLogGroup')
        self.assertNotEqual(0, len(logs[ORBIT_REGION]))

    def test_02_docker_logging(self):
        """Verify docker logs are forwarded to CW:L."""
        for app_region in self.app.regions.values():
            app_region.logging['docker'] = {
                'retention': 7
            }
        # self.provision()

        # Sent a unique request (404 is ok)
        breadcrumb = str(uuid.uuid4())
        self._get(breadcrumb, https=False)

        # Query logs after propagation delay
        time.sleep(10)
        logs = self._get_logs('DockerLogGroup')[ORBIT_REGION]

        # Verify unique token was logged:
        logged_crumb = [log for log in logs if breadcrumb in log['message']]
        self.assertEquals(1, len(logged_crumb))

    def test_03_docker_logging_metric(self):
        for app_region in self.app.regions.values():
            app_region.logging['docker'] = {
                'retention': 7,
                'metrics': {
                    'Count404': {
                        'pattern': '{ $.res.statusCode = 404 }',
                        'value': '1'
                    },
                    'ResponseTime': {
                        'pattern': '{ $.res.responseTime = * }',
                        'value': '$.res.responseTime'
                    }
                }

            }
        self.provision()

    def _get_logs(self, log_group):
        logs = {}
        for region in self.app.regions.keys():
            log_group_arn = self._log_group_arn(region, log_group)
            if not log_group_arn:
                continue
            logs[region] = self._log_events(region, log_group_arn)
        return logs

    def _log_events(self, region, log_group_arn):
        cwl = self.clients.logs(region)

        region_logs = []

        # Don't paginate: recent logs are in the first page
        streams = cwl.describe_log_streams(logGroupName=log_group_arn,
                                           orderBy='LastEventTime',
                                           descending=True)

        for stream in streams.get('logStreams', ()):
            stream_name = stream['logStreamName']
            print(stream_name)
            # Don't paginate: recent logs are in the first page
            events = cwl.get_log_events(
                logGroupName=log_group_arn,
                logStreamName=stream_name,
                startTime=self.start
            )
            for event in events.get('events', ()):
                region_logs.append(event)
        return region_logs

    def _log_group_arn(self, region, log_group):
        cf = self.clients.cloudformation(region)
        resource = cf.describe_stack_resource(
            StackName='sl-test-laika',
            LogicalResourceId=log_group
        )
        return resource.get('StackResourceDetail', {}).get('PhysicalResourceId')
