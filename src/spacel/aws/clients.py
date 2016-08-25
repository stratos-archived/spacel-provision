import boto3
from collections import defaultdict
import logging

logger = logging.getLogger('spacel.aws.clients')


class ClientCache(object):
    """
    Lazy instantiation container for AWS clients.
    """

    def __init__(self):
        self._clients = defaultdict(dict)

    def ec2(self, region):
        """
        Get EC2 client.
        :param region:  AWS region.
        :return: EC2 Client.
        """
        return self._client('ec2', region)

    def cloudformation(self, region):
        """
        Get CloudFormation client.
        :param region:  AWS region.
        :return: CloudFormation Client.
        """
        return self._client('cloudformation', region)

    def s3(self, region):
        """
        Get S3 client.
        :param region:  AWS region.
        :return: S3 Client.
        """
        return self._resource('s3', region)

    def _client(self, client_type, region):
        client_cache = self._clients[client_type]
        cached = client_cache.get(region)
        if cached:
            return cached
        logger.debug('Connecting to %s in %s.', client_type, region)
        client = boto3.client(client_type, region)
        client_cache[region] = client
        return client

    def _resource(self, client_type, region):
        client_cache = self._clients[client_type]
        cached = client_cache.get(region)
        if cached:
            return cached
        logger.debug('Connecting to %s in %s.', client_type, region)
        client = boto3.resource(client_type, region)
        client_cache[region] = client
        return client
