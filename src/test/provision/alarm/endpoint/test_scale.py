from six import u
from spacel.provision.alarm.endpoint.scale import ScaleEndpoints
from test.provision.alarm.endpoint import RESOURCE_NAME, BaseEndpointTest


class TestScaleEndpoints(BaseEndpointTest):
    def setUp(self):
        super(TestScaleEndpoints, self).setUp()
        self.endpoint = ScaleEndpoints()

    def topic_resource(self):
        return 'EndpointScaleTestResourcePolicy'

    def test_add_endpoints_invalid_adjustment(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {
            'adjustment': '0'
        })
        self.assertEquals(0, len(actions))

    def test_add_endpoints_percentage(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {
            'adjustment': '200%'
        })
        self.assertNotEquals(0, len(actions))

    def test_add_endpoints(self):
        actions = self.endpoint.add_endpoints(self.template, RESOURCE_NAME, {
        })
        self.assertNotEquals(0, len(actions))
        self.assertTrue(actions)

    def test_calculate_adjustment_direction_down(self):
        self.endpoint = ScaleEndpoints(direction=-1)
        self.assertEquals(-1, self.endpoint._calculate_adjustment(1))
        self.assertEquals(-1, self.endpoint._calculate_adjustment(-1))
        self.assertEquals(-1, self.endpoint._calculate_adjustment(u('1')))
        self.assertEquals(-1, self.endpoint._calculate_adjustment('1'))

    def test_calculate_adjustment_direction_up(self):
        self.endpoint = ScaleEndpoints(direction=1)
        self.assertEquals(1, self.endpoint._calculate_adjustment(1))
        self.assertEquals(1, self.endpoint._calculate_adjustment(-1))
        self.assertEquals(1, self.endpoint._calculate_adjustment(u('1')))
        self.assertEquals(1, self.endpoint._calculate_adjustment('1'))

    def test_calculate_adjustment_direction_undefined(self):
        self.assertEquals(1, self.endpoint._calculate_adjustment(1))
        self.assertEquals(-1, self.endpoint._calculate_adjustment(-1))
