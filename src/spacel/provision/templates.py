from spacel.aws import AmiFinder
from spacel.provision.template import *


class TemplateCache(object):
    # TODO: finish replacing
    def __init__(self):
        self._ami = AmiFinder()
        self._app = AppTemplate(self._ami)
        self._bastion = BastionTemplate(self._ami)
        self._tables = TablesTemplate()
        self._vpc = VpcTemplate()

    def vpc(self, orbit, region):
        return self._vpc.vpc(orbit, region)

    def bastion(self, orbit, region):
        return self._bastion.bastion(orbit, region)

    def tables(self, orbit):
        return self._tables.tables(orbit)

    def app(self, app, region):
        return self._app.app(app, region)
