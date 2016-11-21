from test_integ import BaseIntegrationTest, ORBIT_REGION


class TestMultiRegion(BaseIntegrationTest):
    def setUp(self):
        super(TestMultiRegion, self).setUp()
        self._second_region()

    def test_01_rds(self):
        """A single RDS instance is shared by two regions."""
        for app_region in self.app.regions.values():
            app_region.databases['postgres'] = {
                'global': ORBIT_REGION
            }
        self.provision()

        self._verify_counter('postgres', post_count=10)
