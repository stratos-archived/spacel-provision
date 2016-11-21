from spacel.model import Orbit
from spacel.model.json.base import BaseJsonModelFactory, NAME, REGIONS


class OrbitJsonModelFactory(BaseJsonModelFactory):
    def orbit(self, params, regions=()):
        """
        Transform Orbit JSON manifest to Orbit.
        :param params: Parsed Orbit JSON manifest.
        :param regions:  Regions.
        :return: Orbit.
        """
        name = params.get(NAME)
        region_params = params.get(REGIONS, ())
        if regions:
            if region_params:
                regions = [region for region in regions
                           if region in region_params]
        else:
            regions = region_params

        orbit = Orbit(name, regions)
        self._set_properties(orbit, params)
        return orbit
