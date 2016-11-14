import logging
from paramiko import (SSHClient, RSAKey, AutoAddPolicy)

from spacel.model.orbit import BASTION_INSTANCE_COUNT

from test_integ import BaseIntegrationTest

# Weak keys are quick to generate; we're only testing!
KEY_BITS = 1024
USER_NAME = 'test-user'

logger = logging.getLogger('spacel.test.ssh_access')


class TestSshAccess(BaseIntegrationTest):
    KEY = None

    @classmethod
    def setUpClass(cls):
        super(TestSshAccess, cls).setUpClass()
        cls.KEY = RSAKey.generate(KEY_BITS)

    def setUp(self):
        super(TestSshAccess, self).setUp()
        self.orbit_params['defaults'][BASTION_INSTANCE_COUNT] = 1
        self.provisioned_app = self.provision()

    def test_01_bastion_login(self):
        """Provision, log in to gateway."""
        encoded_key = 'ssh-rsa %s' % TestSshAccess.KEY.get_base64()
        self.ssh_db.add_key(self.provisioned_app.orbit, USER_NAME, encoded_key)
        self.ssh_db.grant(self.provisioned_app, USER_NAME)

        bastions = self._test_bastions(self.provisioned_app)
        self.assertEquals(1, len(bastions))

    def test_02_bastion_denied(self):
        """Provision, get denied from gateway."""
        self.ssh_db.revoke(self.provisioned_app, USER_NAME)
        bastions = self._test_bastions(self.provisioned_app)
        self.assertEquals(0, len(bastions))

    def _test_bastions(self, app):
        bastions = set()
        for region in app.orbit.regions:
            for bastion_ip in self._bastion_ips(app.orbit, region):
                logger.debug('Connecting to %s...', bastion_ip)
                motd_lines = self._ssh(bastion_ip, 'cat /etc/motd')
                if 'Space Elevator (Debian 8)' in motd_lines:
                    bastions.add(bastion_ip)
        return bastions

    @staticmethod
    def _ssh(bastion_ip, command):
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        lines = []
        try:
            client.connect(bastion_ip,
                           username='space',
                           pkey=TestSshAccess.KEY)
            _, stdout, _ = client.exec_command(command)
            for line in stdout:
                lines.append(line)
        except:
            pass
        finally:
            client.close()
        return lines

    def _bastion_ips(self, orbit, region):
        cf = self.clients.cloudformation(region)
        bastion_stack = '%s-bastion' % orbit.name
        stack = cf.describe_stacks(StackName=bastion_stack)['Stacks'][0]
        bastion_ips = [o['OutputValue'] for o in stack['Outputs']
                       if o['OutputKey'].startswith('ElasticIp')]

        expected_count = orbit._get_param(region, BASTION_INSTANCE_COUNT)
        self.assertEquals(expected_count, len(bastion_ips))
        return bastion_ips
