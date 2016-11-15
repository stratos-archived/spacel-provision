from spacel.model import SpaceApp
from spacel.model.json.base import BaseJsonModelFactory, NAME, REGIONS


class SpaceAppJsonModelFactory(BaseJsonModelFactory):
    def app(self, orbit, params):
        name = params.get(NAME)
        regions = params.get(REGIONS, ())
        app = SpaceApp(orbit, name, regions)
        self._set_properties(app, params)
        return app
