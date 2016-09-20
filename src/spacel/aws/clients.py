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

    def kms(self, region):
        """
        Get KMS client.
        :param region:  AWS region.
        :return: KMS Client.
        """
        return self._client('kms', region)

    def dynamodb(self, region):
        """
        Get DynamoDb client.
        :param region:  AWS region.
        :return: DynamoDb Client.
        """
        return self._client('dynamodb', region)

    def acm(self, region):
        """
        Get AWS Certificate Manager client.
        :param region:  AWS region.
        :return: ACM Client.
        """
        return self._client('acm', region)

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
