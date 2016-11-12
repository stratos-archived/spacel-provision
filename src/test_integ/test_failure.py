from test_integ import BaseIntegrationTest


class TestDeployFailure(BaseIntegrationTest):
    def setUp(self):
        super(TestDeployFailure, self).setUp()
        self.provision()

    def test_unit_does_not_load(self):
        """Bad syntax means unit file won't load."""
        self._set_unit_file('meow')
        self.provision(expected=1)

    def test_unit_does_not_start(self):
        """Valid unit file that fails to start."""
        self._set_unit_file('''[Service]
ExecStart=/bin/false
''')
        self.provision(expected=1)

    def test_fail_elb_health_check(self):
        """Docker unit doesn't expose port, so ELB can't verify."""
        del self.app_params['services']['laika']['ports']
        self.provision(expected=1)
