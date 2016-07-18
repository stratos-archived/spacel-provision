from io import BytesIO
import json
from mock import MagicMock, patch
import unittest

from spacel.aws.ami import AmiFinder

AMI = 'ami-123456'
REGION = 'us-west-2'


class TestAmiFinder(unittest.TestCase):
    def setUp(self):
        self.ami_finder = AmiFinder()

    def test_spacel_ami(self):
        self.ami_finder._ami = MagicMock(return_value=AMI)

        ami = self.ami_finder.spacel_ami(REGION)

        self.assertEqual(AMI, ami)

    @patch('spacel.aws.ami.urlopen')
    def test_ami_found(self, mock_urlopen):
        self._mock_response(mock_urlopen)

        ami = self.ami_finder.spacel_ami(REGION)

        self.assertEqual(AMI, ami)

    @patch('spacel.aws.ami.urlopen')
    def test_ami_found_cache(self, mock_urlopen):
        self._mock_response(mock_urlopen)

        self.ami_finder.spacel_ami(REGION)
        self.ami_finder.spacel_ami(REGION)

        self.assertEqual(1, mock_urlopen.call_count)

    @staticmethod
    def _mock_response(mock_urlopen):
        response_bytes = json.dumps({
            REGION: AMI
        }).encode('utf-8')
        mock_urlopen.return_value = BytesIO(response_bytes)
