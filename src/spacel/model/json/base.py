import logging

logger = logging.getLogger('spacel.model.json')

NAME = 'name'
REGIONS = 'regions'
ALL = 'all'

CUSTOM_KEYS = {
    'orbit',
    'services'
}


class BaseJsonModelFactory(object):
    @staticmethod
    def _set_properties(obj, params):
        defaults = params.get(ALL, {})
        region_params = {region: params.get(region, {})
                         for region in obj.regions}
        for region, region_obj in obj.regions.items():
            params = region_params[region]
            for region_key in vars(region_obj):
                if region_key in CUSTOM_KEYS or region_key.startswith('_'):
                    continue
                value = params.get(region_key)
                if value is None:
                    value = defaults.get(region_key)
                if value is not None:
                    setattr(region_obj, region_key, value)
