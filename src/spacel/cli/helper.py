import json
import logging
from os.path import isfile, isdir

import boto3
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import urlparse
from six.moves.urllib.request import urlopen

from spacel.main import setup_logging
from spacel.model import Orbit, SpaceApp
from spacel.model.files import SpaceAppFilesModelFactory
from spacel.model.json import OrbitJsonModelFactory, SpaceAppJsonModelFactory

logger = logging.getLogger('spacel.cli')

LOG_LEVELS = (
    'DEBUG', 'debug',
    'INFO', 'info',
    'WARNING', 'warning',
    'ERROR', 'error',
    'CRITICAL', 'critical'
)


class ClickHelper(object):
    def __init__(self):
        self._orbit_factory = OrbitJsonModelFactory()
        self._app_json_factory = SpaceAppJsonModelFactory()
        self._app_files_factory = SpaceAppFilesModelFactory()
        self._cache = {}

    @staticmethod
    def setup_logging(log_level):
        level = logging.getLevelName(log_level.upper())
        setup_logging(level)

    def orbit(self, orbit_param, regions=()):
        orbit_params = self.read_manifest(orbit_param, 'orbit')
        if orbit_params:
            return self._orbit_factory.orbit(orbit_params, regions=regions)
        return Orbit(name=orbit_param, regions=regions)

    def app(self, orbit, app_param, version=None):
        app = self._app(orbit, app_param)
        if app and version:
            for app_region in app.regions.values():
                for service in app_region.services.values():
                    service.version = version
        return app

    def _app(self, orbit, app_param):
        app_params = self.read_manifest(app_param, 'app')
        if app_params:
            return self._app_json_factory.app(orbit, app_params)
        url = urlparse(app_param)
        if isdir(url.path):
            return self._app_files_factory.app(orbit, url.path)
        return SpaceApp(orbit, name=app_param)

    def read_manifest(self, path, label):
        """
        Read JSON manifest from path.
        :param path: Path (file, http://, s3://).
        :param label: Label for manifest (for user-friendly errors).
        :return: Parsed JSON manifest, None if not found.
        """
        if not path:
            return None

        cached = self._cache.get(path)
        if cached:
            return cached

        url = urlparse(path)
        if url.scheme in ('http', 'https'):
            try:
                opened = urlopen(path)
                json_body = opened.read()
            except HTTPError as e:
                logger.warning('Unable to read "%s" manifest from %s: %s - %s',
                               label,
                               path,
                               e.code,
                               e.msg)
                return None
        elif url.scheme == 's3':
            region, bucket, key = self._parse_s3(url)
            s3_resource = boto3.resource('s3', region)
            json_body = s3_resource.Object(bucket, key).get()['Body'].read()
        elif isfile(url.path):
            with open(path, 'rb') as file_in:
                json_body = file_in.read()
        elif isdir(url.path):  # pragma: no cover
            return None
        else:
            logger.debug('Unable to parse "%s" manifest path: %s', label, path)
            return None

        if json_body:
            try:
                manifest = json.loads(json_body.decode('utf-8'))
                self._cache[path] = manifest
                return manifest
            except ValueError as e:
                logger.error('Unable to parse "%s" JSON: %s', label, e)
        return None

    def write_manifest(self, path, label, manifest):
        """
        Write JSON manifest to path.
        :param path: Path (file, http://, s3://).
        :param label: Label for manifest (for user-friendly errors).
        :param manifest: Manifest.
        """
        json_body = json.dumps(manifest, indent=2, sort_keys=True)

        updated = False
        url = urlparse(path)
        if isfile(url.path):
            with open(path, 'w') as file_out:
                file_out.write(json_body)
            updated = True
        else:
            logger.debug('Unable to parse "%s" manifest path: %s', label, path)

        if updated:
            self._cache[path] = manifest

        return updated

    @staticmethod
    def _parse_s3(s3_url):
        key = s3_url.path[1:]

        hostname = s3_url.hostname
        aws_pos = hostname.find('.amazonaws.com')
        if aws_pos != -1:
            host_prefix = hostname[:aws_pos]
            if '.' in host_prefix:
                bucket, host_prefix = host_prefix.split('.', 1)
            else:
                _, bucket, key = s3_url.path.split('/', 2)
            region = host_prefix.replace('s3.', '').replace('s3-', '')
        else:
            region = 'us-east-1'
            bucket = hostname

        return region, bucket, key
