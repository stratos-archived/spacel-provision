import boto3
import logging

logger = logging.getLogger('spacel')


class ClientCache(object):
    """
    Lazy instantiation container for EC2 client.
    """

    def __init__(self):
        self._cloudformation = {}
        self._ec2 = {}

    def ec2(self, region):
        """
        Get EC2 client.
        :param region:  AWS region.
        :return: EC2 Client.
        """
        cached = self._ec2.get(region)
        if cached:
            return cached
        logger.debug('Connecting to EC2 in %s.', region)
        ec2 = boto3.client('ec2', region)
        self._ec2[region] = ec2
        return ec2

    def cloudformation(self, region):
        cached = self._cloudformation.get(region)
        if cached:
            return cached
        logger.debug('Connecting to CloudFormation in %s.', region)
        cloudformation = boto3.client('cloudformation', region)
        self._cloudformation[region] = cloudformation
        return cloudformation
