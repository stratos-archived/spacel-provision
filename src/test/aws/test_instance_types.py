import unittest
from spacel.model.aws import INSTANCE_VOLUMES

# AWS < Heinz
INSTANCE_TYPE_COUNT = 54


class TestInstanceTypes(unittest.TestCase):
    def test_instance_volumes(self):
        self.assertEqual(INSTANCE_TYPE_COUNT, len(INSTANCE_VOLUMES))
