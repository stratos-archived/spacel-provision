import logging
import os
import sys

from spacel.aws import AmiFinder, ClientCache
from spacel.args import parse_args
from spacel.model import SpaceApp, Orbit
from spacel.provision import (ChangeSetEstimator, CloudProvisioner,
                              LambdaUploader, ProviderOrbitFactory)

from spacel.provision.template import (AppTemplate, BastionTemplate,
                                       TablesTemplate, VpcTemplate)
from spacel.provision.alarm import AlertFactory


def main(args, in_stream):
    orbit_json, app_json = parse_args(args, in_stream)
    if not orbit_json or not app_json:
        return -1

    orbit = Orbit(orbit_json)
    app = SpaceApp(orbit, app_json)

    clients = ClientCache()

    # Lambda function storage
    lambda_bucket = os.environ.get('LAMBDA_BUCKET')
    lambda_region = os.environ.get('LAMBDA_REGION', 'us-west-2')
    lambda_up = LambdaUploader(clients, lambda_region, lambda_bucket)
    pagerduty_default = os.environ.get('WEBHOOKS_PAGERDUTY')
    alert_factory = AlertFactory.get(pagerduty_default, lambda_up)

    # Templates:
    ami_finder = AmiFinder()
    app_template = AppTemplate(ami_finder, alert_factory)
    bastion_template = BastionTemplate(ami_finder)
    tables_template = TablesTemplate()
    vpc_template = VpcTemplate()

    change_sets = ChangeSetEstimator()
    orbit_factory = ProviderOrbitFactory.get(clients, change_sets, vpc_template,
                                             bastion_template,
                                             tables_template)
    orbit_factory.get_orbit(orbit)

    provisioner = CloudProvisioner(clients, change_sets, app_template)
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
