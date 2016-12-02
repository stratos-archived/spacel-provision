import click

from spacel.aws import AmiFinder, ClientCache
from spacel.cli.helper import ClickHelper, LOG_LEVELS
from spacel.model.aws import VALID_REGIONS
from spacel.provision import (ChangeSetEstimator, LambdaUploader,
                              TemplateUploader)
from spacel.provision.app import (AppSpotTemplateDecorator,
                                  CloudWatchLogsDecorator,
                                  IngressResourceFactory)
from spacel.provision.app import SpaceElevatorAppFactory
from spacel.provision.app.alarm import AlarmFactory
from spacel.provision.app.db import CacheFactory, RdsFactory
from spacel.provision.orbit.provider import ProviderOrbitFactory
from spacel.provision.template import (AppTemplate, BastionTemplate,
                                       TablesTemplate, VpcTemplate)
from spacel.security import (AcmCertificates, KmsCrypto, KmsKeyFactory,
                             PasswordManager)

SPACEL_AGENT_CHANNELS = (
    'stable',
    'latest'
)


@click.group()
def provision_cmd():  # pragma: no cover
    pass


@provision_cmd.command(name='provision',
                       help='Provision/upgrade resources for deployment.')
@click.option('--orbit', type=click.STRING, help='Orbit name/path.',
              required=True)
@click.option('--app', type=click.STRING, help='App name/path.', required=True)
@click.option('--region', '-r', multiple=True, type=click.Choice(VALID_REGIONS),
              help='Regions to encrypt secret in.')
@click.option('--lambda-bucket', type=click.STRING, envvar='LAMBDA_BUCKET',
              help='Bucket for temporary Lambda storage.')
@click.option('--lambda-region', type=click.Choice(VALID_REGIONS),
              envvar='LAMBDA_REGION', help='Region of Lambda bucket.')
@click.option('--template-bucket', type=click.STRING, envvar='TEMPLATE_BUCKET',
              help='Bucket for temporary CloudFormation storage.')
@click.option('--template-region', type=click.Choice(VALID_REGIONS),
              envvar='TEMPLATE_REGION', help='Region of CloudFormation bucket.')
@click.option('--pagerduty-default', type=click.STRING,
              envvar='WEBHOOKS_PAGERDUTY', help='PagerDuty default endpoint.')
@click.option('--pagerduty-api-key', type=click.STRING,
              envvar='PAGERDUTY_API_KEY', help='PagerDuty API key.')
@click.option('--spacel-agent-channel',
              type=click.Choice(SPACEL_AGENT_CHANNELS), default='stable',
              envvar='SPACEL_AGENT_CHANNEL', help='Spacel agent AMI channel.')
@click.option('--spacel-agent-cache-bust', is_flag=True,
              envvar='SPACEL_AGENT_CACHE_BUST',
              help='Spacel agent AMI cache bust.')
@click.option('--log-level', default='INFO', type=click.Choice(LOG_LEVELS),
              help='Log level')
@click.option('--version', type=click.STRING, help='Version to deploy')
def provision_cli(orbit, app, region, lambda_bucket, lambda_region,
                  template_bucket, template_region, pagerduty_default,
                  pagerduty_api_key, spacel_agent_channel,
                  spacel_agent_cache_bust, log_level,
                  version):  # pragma: no cover
    provision_services(orbit, app, region,
                       lambda_bucket, lambda_region,
                       template_bucket, template_region,
                       pagerduty_default, pagerduty_api_key,
                       spacel_agent_channel, spacel_agent_cache_bust,
                       log_level, version)


def provision_services(orbit_path, app_path, regions,
                       lambda_bucket, lambda_region,
                       template_bucket, template_region,
                       pagerduty_default, pagerduty_api_key,
                       spacel_agent_channel, spacel_agent_cache_bust,
                       log_level, version):
    helper = ClickHelper()
    helper.setup_logging(log_level)

    # Parameters:
    orbit = helper.orbit(orbit_path, regions)
    if not orbit.valid:
        return -1
    app = helper.app(orbit, app_path, version)
    if not app.valid:
        return -1

    return provision(app, lambda_bucket, lambda_region, template_bucket,
                     template_region, pagerduty_default, pagerduty_api_key,
                     spacel_agent_channel, spacel_agent_cache_bust)


def provision(app,
              lambda_bucket=None,
              lambda_region=None,
              template_bucket=None,
              template_region=None,
              pagerduty_default=None,
              pagerduty_api_key=None,
              spacel_agent_channel=None,
              spacel_agent_cache_bust=False):  # pragma: no cover
    clients = ClientCache()

    # Lambda function storage
    lambda_up = LambdaUploader(clients, lambda_region, lambda_bucket)
    # CloudFormation template storage
    template_bucket = template_bucket or lambda_bucket
    template_region = template_region or lambda_region
    template_up = TemplateUploader(clients, template_region, template_bucket)
    alarm_factory = AlarmFactory.get(pagerduty_default,
                                     pagerduty_api_key,
                                     lambda_up)
    ingress_factory = IngressResourceFactory(clients)
    kms_key_factory = KmsKeyFactory(clients)
    kms_crypto = KmsCrypto(clients, kms_key_factory)
    password_manager = PasswordManager(clients, kms_crypto)
    cache_factory = CacheFactory(ingress_factory)
    rds_factory = RdsFactory(clients, ingress_factory, password_manager)
    cw_logs = CloudWatchLogsDecorator()
    # Templates:
    ami_finder = AmiFinder(spacel_agent_channel,
                           cache_bust=spacel_agent_cache_bust)
    app_spot = AppSpotTemplateDecorator()
    acm = AcmCertificates(clients)
    app_template = AppTemplate(ami_finder, alarm_factory, cache_factory,
                               rds_factory, app_spot, acm, kms_key_factory,
                               cw_logs, ingress_factory)
    bastion_template = BastionTemplate(ami_finder)
    tables_template = TablesTemplate()
    vpc_template = VpcTemplate()
    change_sets = ChangeSetEstimator()
    orbit_factory = ProviderOrbitFactory.get(clients, change_sets, template_up,
                                             vpc_template,
                                             bastion_template,
                                             tables_template)
    orbit_factory.orbit(app.orbit)
    provisioner = SpaceElevatorAppFactory(clients, change_sets, template_up,
                                          app_template)
    if not provisioner.app(app):
        return 1
    return 0
