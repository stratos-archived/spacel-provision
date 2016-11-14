import logging

logger = logging.getLogger('spacel.model')

NAME = 'name'
DEFAULTS = 'defaults'
REGIONS = 'regions'

# https://github.com/pebble/vz-spacel-agent/blob/master/spacel-agent.yml
# see: plugins.ec2_publish.regions ; 'us-west-2' is automatic
VALID_REGIONS = (
    'us-west-2',
    'us-east-1',
    'eu-west-1',
    'ap-southeast-1',
    'sa-east-1',
    'ap-northeast-1'
)


class BaseModelObject(object):
    def __init__(self, params=None, defaults=None):
        self._params = params or {}
        self._defaults = defaults or {}
        self.valid = True

        self.name = None  # Temporary store
        self.name = self._required(NAME)
        self.regions = self._regions()

    def _regions(self, valid_regions=VALID_REGIONS, default_regions=None):
        raw_list = self._params.get(REGIONS)
        if not raw_list:
            if default_regions:
                return default_regions
            self._on_missing('regions')
            return []

        for item in list(raw_list):
            if item not in valid_regions:
                self.valid = False
                logger.warn('%s has invalid "regions" value: "%s". Only: %s',
                            self._label(), item, ', '.join(valid_regions))
                raw_list.remove(item)
        return raw_list

    def _required(self, key):
        """
        Get a required parameter. Updates `.valid` property.
        :param key:  Parameter key.
        :return: Parameter value, None if not found.
        """
        value = self._params.get(key)
        if value:
            return value

        self._on_missing(key)
        return None

    def _on_missing(self, key):
        self.valid = False
        logger.warn('%s is missing %s.', self._label(), key)

    def _label(self):
        obj_label = self.__class__.__name__
        if self.name:
            obj_label += ' ' + self.name
        return obj_label

    def _get_param(self, region, key):
        """
        Get a parameter value, customized for a region.
        :param region:  Region name.
        :param key:  Parameter key.
        :return: Parameter value, None if not available.
        """
        region_map = self._params.get(region)
        if region_map:
            region_value = region_map.get(key)
            if region_value is not None:
                return region_value

        defaults_map = self._params.get(DEFAULTS)
        if defaults_map:
            defaults_value = defaults_map.get(key)
            if defaults_value is not None:
                return defaults_value
        return self._defaults.get(key)
