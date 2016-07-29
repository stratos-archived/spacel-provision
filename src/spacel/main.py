import logging
import sys

from spacel.aws import ClientCache
from spacel.args import parse_args
from spacel.model import SpaceApp, Orbit
from spacel.provision import (ChangeSetEstimator, CloudProvisioner,
                              ProviderOrbitFactory, TemplateCache)


def main(args, in_stream):
    orbit_json, app_json = parse_args(args, in_stream)
    if not orbit_json or not app_json:
        return -1

    orbit = Orbit(orbit_json)
    app = SpaceApp(orbit, app_json)

    clients = ClientCache()
    templates = TemplateCache()
    change_sets = ChangeSetEstimator()

    orbit_factory = ProviderOrbitFactory.get(clients, change_sets, templates)
    orbit_factory.get_orbit(orbit)

    provisioner = CloudProvisioner(clients, change_sets, templates)
    provisioner.app(app)
    return 0


if __name__ == '__main__':  # pragma: no cover
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('spacel').setLevel(logging.DEBUG)

    result = main(sys.argv[1:], sys.stdin)
    sys.exit(result)
