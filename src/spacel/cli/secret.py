import logging
import sys

import click
from botocore.exceptions import ClientError

from spacel.aws import ClientCache
from spacel.cli.helper import ClickHelper, LOG_LEVELS
from spacel.model.aws import VALID_REGIONS
from spacel.security import KmsCrypto, KmsKeyFactory

logger = logging.getLogger('spacel.cli.secret')


@click.group()
def secret_cmd():  # pragma: no cover
    pass


@secret_cmd.command(help='Encrypt secrets.')
@click.option('--orbit', type=click.STRING, help='Orbit name/path.',
              envvar='SPACEL_ORBIT', required=True)
@click.option('--app', type=click.STRING, help='App name/path.',
              envvar='SPACEL_APP', required=True, default='/pwd')
@click.option('--region', '-r', multiple=True, type=click.Choice(VALID_REGIONS),
              help='Regions to encrypt secret in.')
@click.option('--create', '--create-key', is_flag=True,
              help='Create KMS key if not found.')
@click.option('--modify', '-m', is_flag=True,
              help='Write secrets directly to file.')
@click.option('--key', type=click.STRING, help='Environment variable key.')
@click.option('--value', type=click.STRING, help='Secret value')
@click.option('--log-level', default='INFO', type=click.Choice(LOG_LEVELS),
              envvar='SPACEL_LOG_LEVEL', help='Log level')
def secret(orbit, app, region, create_key, modify, key, value,
           log_level):  # pragma: no cover
    handle_secret(orbit, app, region, create_key, modify, key, value, log_level,
                  sys.stdin)


def handle_secret(orbit_path, app_path, regions, create_key, modify, key, value,
                  log_level, in_stream):
    helper = ClickHelper()
    helper.setup_logging(log_level)

    # What to encrypt:
    plaintext = get_plaintext(key, value, in_stream)
    if not plaintext:
        logger.error('Could not find secret, use --key and/or --value!')
        return False

    # What key to use, where:
    orbit = helper.orbit(orbit_path, regions)
    app = helper.app(orbit, app_path)
    if not app.regions:
        logger.error('Regions not specified.')
        return False

    # Perform encryption:
    cipher_texts = encrypt(app, plaintext, create_key)
    if not cipher_texts:
        return False

    # Update manifest in-place, or dump to stdout:
    if modify and update_manifest(helper, app_path, key, cipher_texts):
        logger.debug('Manifest "%s" updated.', app_path)
    else:
        for payload in cipher_texts.values():
            print(payload.json())
    return True


def get_plaintext(key, value, stream_in):
    if value == '-':
        if key:
            logger.warning('Key "%s" ignored when reading value from stdin.',
                           key)
        return stream_in.read()
    if key and value:
        return '%s=%s' % (key, value)
    return value


def encrypt(app, plaintext, create_key):
    orbit = app.orbit
    clients = ClientCache()
    kms_key = KmsKeyFactory(clients)
    kms_crypto = KmsCrypto(clients, kms_key)
    logger.info('Encrypting secret to %s@%s in %s regions...', app.name,
                orbit.name, len(app.regions))
    payloads = {}
    for app_region in app.regions.values():
        try:
            encrypted_payload = kms_crypto.encrypt(app_region, plaintext,
                                                   create_key=create_key)
            payloads[app_region.region] = encrypted_payload
        except ClientError as e:
            e_message = e.response['Error'].get('Message', '')
            logger.error(e_message)
            return None
    logger.info('Encrypted secret to %s@%s in %s regions...', app.name,
                orbit.name, len(app.regions))
    return payloads


def update_manifest(helper, app_json_path, key, cipher_texts):
    if not key:
        logger.warning('Can not modify manifest file without key.')
        return False

    app_params = helper.read_manifest(app_json_path, 'app')

    # Treat
    if len(cipher_texts) == 1:
        cipher_texts['all'] = next(iter(cipher_texts.values()))

    # Update body:
    updated = False
    for region, region_params in app_params.items():
        cipher_text = cipher_texts.get(region)
        if not cipher_text:
            continue

        region_services = region_params.get('services', {})
        for service_params in region_services.values():
            service_environment = service_params.get('environment')
            if not service_environment:
                service_params['environment'] = service_environment = {}
            service_environment[key] = cipher_text.obj()
            updated = True

    # Write to path (or dump to stdout)
    if updated:
        return helper.write_manifest(app_json_path, 'app', app_params)
    return updated
