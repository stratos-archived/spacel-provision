import json
import unittest

from mock import patch, MagicMock
from six import BytesIO, StringIO
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import urlparse

from spacel.cli.helper import ClickHelper
from test import ORBIT_NAME

HTTP_ORBIT = 'http://test.com/orbit'
FILE_ORBIT = 'test.json'

MAP_VALUES = {'name': ORBIT_NAME}
MAP_ENCODED = json.dumps(MAP_VALUES).encode('utf-8')


class TestClickHelper(unittest.TestCase):
    def setUp(self):
        self.helper = ClickHelper()

    def test_setup_logging(self):
        self.helper.setup_logging('CRITICAL')

    def test_orbit_from_manifest(self):
        self.helper.read_manifest = MagicMock(return_value=MAP_VALUES)
        orbit = self.helper.orbit('from-manifest')
        self.assertEquals(ORBIT_NAME, orbit.name)

    def test_orbit_from_parameters(self):
        self.helper.read_manifest = MagicMock(return_value=None)
        orbit = self.helper.orbit('from-parameters')
        self.assertEquals('from-parameters', orbit.name)

    def test_app_from_manifest(self):
        self.helper.read_manifest = MagicMock(return_value=MAP_VALUES)
        orbit = MagicMock()
        app = self.helper.app(orbit, 'from-manifest')
        self.assertEquals(ORBIT_NAME, app.name)

    def test_app_from_parameters(self):
        self.helper.read_manifest = MagicMock(return_value=None)
        orbit = MagicMock()
        app = self.helper.app(orbit, 'from-parameters')
        self.assertEquals('from-parameters', app.name)

    def test_read_manifest_noop(self):
        manifest = self.helper.read_manifest(None, 'test')
        self.assertIsNone(manifest)

    @patch('spacel.cli.helper.urlopen')
    def test_read_manifest_http(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(MAP_ENCODED)

        manifest = self.helper.read_manifest(HTTP_ORBIT, 'test')

        self.assertEquals(MAP_VALUES, manifest)
        mock_urlopen.assert_called_once_with(HTTP_ORBIT)

    @patch('spacel.cli.helper.open')
    @patch('spacel.cli.helper.isfile')
    def test_read_manifest_file(self, mock_isfile, mock_open):
        mock_isfile.return_value = True
        mock_open.return_value = BytesIO(MAP_ENCODED)
        manifest = self.helper.read_manifest(FILE_ORBIT, 'test')
        self.assertEquals(MAP_VALUES, manifest)

    @patch('spacel.cli.helper.urlopen')
    def test_read_manifest_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(HTTP_ORBIT, 404, 'Kaboom', {},
                                             None)

        manifest = self.helper.read_manifest(HTTP_ORBIT, 'test')
        self.assertIsNone(manifest)

    @patch('spacel.cli.helper.boto3')
    def test_read_manifest_s3(self, mock_boto):
        s3_resource = MagicMock()
        s3_resource.Object.return_value.get.return_value = \
            {'Body': BytesIO(MAP_ENCODED)}

        mock_boto.resource.return_value = s3_resource
        self.helper._parse_s3 = MagicMock(return_value=('us-west-2', 2, 3))

        manifest = self.helper.read_manifest('s3://bucket/key.txt', 'test')

        self.assertEquals(MAP_VALUES, manifest)
        mock_boto.resource.assert_called_with('s3', 'us-west-2')

    def test_read_manifest_not_supported(self):
        manifest = self.helper.read_manifest('magnet:?', 'test')
        self.assertIsNone(manifest)

    @patch('spacel.cli.helper.urlopen')
    def test_read_manifest_empty(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO(''.encode('utf-8'))
        manifest = self.helper.read_manifest(HTTP_ORBIT, 'test')
        self.assertIsNone(manifest)

    @patch('spacel.cli.helper.urlopen')
    def test_read_manifest_cache(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO('{"foo":"bar"}'.encode('utf-8'))
        self.helper.read_manifest(HTTP_ORBIT, 'test')
        self.helper.read_manifest(HTTP_ORBIT, 'test')

        mock_urlopen.assert_called_once_with(HTTP_ORBIT)

    @patch('spacel.cli.helper.urlopen')
    def test_read_manifest_bad_json(self, mock_urlopen):
        mock_urlopen.return_value = BytesIO('kaboom'.encode('utf-8'))
        manifest = self.helper.read_manifest(HTTP_ORBIT, 'test')
        self.assertIsNone(manifest)

    def test_parse_s3_bucket_only(self):
        region, bucket, key = self._parse_s3('s3://bucket/key.txt')

        self.assertEquals('us-east-1', region)
        self.assertEquals('bucket', bucket)
        self.assertEquals('key.txt', key)

    def test_parse_s3_region_bucket_in_path(self):
        region, bucket, key = self._parse_s3(
            's3://s3-us-west-2.amazonaws.com/bucket/key.txt')

        self.assertEquals('us-west-2', region)
        self.assertEquals('bucket', bucket)
        self.assertEquals('key.txt', key)

    def test_parse_s3_region_bucket_in_host(self):
        region, bucket, key = self._parse_s3(
            's3://bucket.s3.us-west-2.amazonaws.com/key.txt')

        self.assertEquals('us-west-2', region)
        self.assertEquals('bucket', bucket)
        self.assertEquals('key.txt', key)

    @patch('spacel.cli.helper.open')
    def test_write_manifest_not_supported(self, mock_open):
        written = self.helper.write_manifest('magnet:?', 'test', {})
        self.assertFalse(written)
        mock_open.assert_not_called()

    @patch('spacel.cli.helper.open')
    @patch('spacel.cli.helper.isfile')
    def test_write_manifest(self, mock_isfile, mock_open):
        mock_isfile.return_value = True
        buf = StringIO()
        mock_open.return_value = buf
        written = self.helper.write_manifest(FILE_ORBIT, 'test', {})
        self.assertTrue(written)
        mock_open.assert_called_once_with(FILE_ORBIT, 'w')

    def _parse_s3(self, url):
        return self.helper._parse_s3(urlparse(url))
