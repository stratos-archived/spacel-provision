import json
import logging
from six.moves.urllib.request import urlopen

SPACEL_URL = 'https://ami.pbl.io/spacel/%s.json'

logger = logging.getLogger('spacel.aws.ami')


class AmiFinder(object):
    def __init__(self):
        self._channel = 'stable'
        self._cache = {}

    def spacel_ami(self, region):
        ami = self._ami(SPACEL_URL, region)
        logger.debug('Found SpaceL AMI %s in %s', ami, region)
        return ami

    def _ami(self, url, region):
        url %= self._channel
        manifest = self._cache.get(url)
        if not manifest:
            logger.debug('AMI manifest %s not cached, fetching...', url)
            opened = urlopen(url)
            manifest = json.loads(opened.read().decode('utf-8'))
            self._cache[url] = manifest
        return manifest.get(region)
