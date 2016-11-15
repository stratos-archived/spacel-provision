from spacel.model import Orbit
from spacel.model.json.base import BaseJsonModelFactory, NAME, REGIONS


class OrbitJsonModelFactory(BaseJsonModelFactory):
    def orbit(self, params):
        name = params.get(NAME)
        regions = params.get(REGIONS, ())
        orbit = Orbit(name, regions)
        self._set_properties(orbit, params)
        return orbit
