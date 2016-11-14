import logging
from botocore.exceptions import ClientError

logger = logging.getLogger('spacel.security.kms_key')


class KmsKeyFactory(object):
    def __init__(self, clients):
        self._clients = clients

    @staticmethod
    def get_key_alias(app):
        """
        Get KMS alias for an application key.
        :param app: Application.
        :return: Key alias.
        """
        return 'alias/%s-%s' % (app.orbit.name, app.name)

    def get_key(self, app, region, create=True):
        """
        Get a KMS key ARN, creating if necessary.
        :param app: App descriptor.
        :param region: Region.
        :param create: Create key if it does not exist.
        :return: KMS key ARN.
        """
        alias_name = self.get_key_alias(app)
        logger.debug('Finding key for "%s" in %s.', alias_name, region)
        try:
            kms = self._clients.kms(region)
            existing_key = kms.describe_key(KeyId=alias_name)
            logger.debug('Found existing key "%s" in %s.', alias_name, region)
            existing_key = existing_key['KeyMetadata']
            key_arn = existing_key['Arn']
            if not existing_key['Enabled']:
                logger.warning('Key %s is disabled.', key_arn)
                return None
            return key_arn
        except ClientError as e:
            e_message = e.response['Error'].get('Message', '')
            if 'Invalid keyId' not in e_message and \
                    'is not found' not in e_message:
                raise e

        if create:
            logger.debug('Unable to find key "%s", creating...', alias_name)
            return self.create_key(app, region)
        else:
            logger.debug('Unable to find key "%s".', alias_name)
            return None

    def create_key(self, app, region):
        """
        Get a KMS key ARN, assuming it doesn't already exist.
        :param app: App descriptor.
        :param region: Region.
        :return: KMS key ARN.
        """
        alias_name = self.get_key_alias(app)

        kms = self._clients.kms(region)
        new_key = kms.create_key()
        key_arn = new_key['KeyMetadata']['Arn']

        # Key created, set alias:
        try:
            kms.create_alias(
                AliasName=alias_name,
                TargetKeyId=key_arn
            )
        except ClientError as e:
            # Key created, but couldn't get alias: cleanup.
            logger.warning('Error applying alias, deleting orphan key: "%s".',
                           key_arn)
            kms.schedule_key_deletion(
                KeyId=key_arn,
                PendingWindowInDays=7
            )
            raise e
        logger.debug('Created key "%s" in %s.', alias_name, region)
        return key_arn
