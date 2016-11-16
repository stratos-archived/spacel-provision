import json
import logging
import time

from six.moves.urllib.request import urlopen

SPACEL_URL = 'https://ami.pbl.io/spacel/%s.json'

logger = logging.getLogger('spacel.aws.ami')


class AmiFinder(object):
    def __init__(self, channel=None, cache_bust=None):
        self._channel = channel or 'stable'
        self.cache_bust = cache_bust
        self._cache = {}

    def spacel_ami(self, region):
        ami = self._ami(SPACEL_URL, region)
        logger.debug('Found SpaceL AMI %s in %s', ami, region)
        return ami

    def _ami(self, url, region):
        url %= self._channel
        if not self.cache_bust:
            manifest = self._cache.get(url)
            if manifest:
                return manifest.get(region)
            logger.debug('AMI manifest %s not cached, fetching...', url)
        else:
            url += '?cache=%s' % time.time()
        opened = urlopen(url)
        manifest = json.loads(opened.read().decode('utf-8'))
        if not self.cache_bust:
            self._cache[url] = manifest
        return manifest.get(region)
