import unittest
from mock import patch, MagicMock

from spacel.aws.clients import ClientCache

from test import ORBIT_REGION


class TestClientCache(unittest.TestCase):
    def setUp(self):
        self.clients = ClientCache()

    @patch('spacel.aws.clients.boto3')
    def test_cloudformation(self, mock_boto3):
        self.clients.cloudformation(ORBIT_REGION)
        mock_boto3.client.assert_called_once_with('cloudformation', ORBIT_REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2(self, mock_boto3):
        self.clients.ec2(ORBIT_REGION)
        mock_boto3.client.assert_called_once_with('ec2', ORBIT_REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2_cached(self, mock_boto3):
        self.clients.ec2(ORBIT_REGION)
        self.clients.ec2(ORBIT_REGION)
        self.assertEqual(1, mock_boto3.client.call_count)

    @patch('spacel.aws.clients.boto3')
    def test_s3(self, mock_boto3):
        self.clients.s3(ORBIT_REGION)
        mock_boto3.resource.assert_called_once_with('s3', ORBIT_REGION)

    @patch('spacel.aws.clients.boto3')
    def test_s3_cached(self, mock_boto3):
        self.clients.s3(ORBIT_REGION)
        self.clients.s3(ORBIT_REGION)
        self.assertEqual(1, mock_boto3.resource.call_count)

    def test_kms(self):
        self.clients._client = MagicMock()
        self.clients.kms(ORBIT_REGION)
        self.clients._client.assert_called_with('kms', ORBIT_REGION)

    def test_dynamodb(self):
        self.clients._client = MagicMock()
        self.clients.dynamodb(ORBIT_REGION)
        self.clients._client.assert_called_with('dynamodb', ORBIT_REGION)

    def test_acm(self):
        self.clients._client = MagicMock()
        self.clients.acm(ORBIT_REGION)
        self.clients._client.assert_called_with('acm', ORBIT_REGION)
