import logging
import re

from botocore.exceptions import ClientError

from spacel.provision import clean_name
from spacel.model.orbit import PRIVATE_NETWORK

IP_BLOCK = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,3}'
logger = logging.getLogger('spacel.provision.ingress_resource')


class IngressResourceFactory(object):
    def __init__(self, clients):
        self._clients = clients

    def ingress_resources(self, orbit, region, start_port, clients,
                          protocol='TCP', end_port=None, sg_ref='Sg'):
        """
        Return ingress resources for access from a list of clients.
        :param orbit:  Orbit definition.
        :param region: Region.
        :param start_port: First port to open
        :param clients: Client list.
        :param protocol: Protocol.
        :param end_port: Last port to open (defaults to start_port if not set).
        :param sg_ref: Security group name.
        :return: dict of {resource_name: cloudformation_resource}
        """
        # Parameter normalization:
        if not end_port:
            end_port = start_port

        # Common properties:
        ingress_properties = {
            'IpProtocol': protocol,
            'FromPort': start_port,
            'ToPort': end_port,
            'GroupId': {'Ref': sg_ref}
        }

        # Accumulator and helper function to accumulate:
        ingress_resources = {}

        def ingress_resource(name, **kwargs):
            kwargs.update(ingress_properties)
            resource_name = 'Ingress%s%s%s%sto%s' % (sg_ref, clean_name(name),
                                                     protocol, start_port,
                                                     end_port)

            ingress_resources[resource_name] = {
                'Type': 'AWS::EC2::SecurityGroupIngress',
                'Properties': kwargs
            }

        # Clients can be...
        for client in clients:
            # An IP block:
            if re.match(IP_BLOCK, client):
                logger.debug('Adding access from %s.', client)
                ingress_resource(client, CidrIp=client)
                continue

            # This orbit region:
            if client == region:
                network = '%s.0.0/16' % orbit.get_param(region, PRIVATE_NETWORK)
                ingress_resource('Orbit%s' % client, CidrIp=network)
                continue

            # Another orbit region (NAT-ed instances in that region):
            if client in orbit.regions:
                logger.debug('Adding access from %s in %s.', orbit.name, client)
                eips = self._app_eips(orbit, region, client, eips=None)
                if eips:
                    for eip_index, eip in enumerate(eips):
                        eip_index += 1
                        if eip:
                            ingress_resource('ElasticIp%s%s' % (client,
                                                                eip_index),
                                             CidrIp='%s/32' % eip)
                else:
                    for nat_index, nat_eip in orbit.nat_eips(client).items():
                        if nat_eip:
                            ingress_resource('Nat%s%s' % (client, nat_index),
                                             CidrIp='%s/32' % nat_eip)
                continue

            # An application in the same orbit:
            sg_id = self._app_sg(orbit, region, client)
            if sg_id:
                ingress_resource('App%s' % client, SourceSecurityGroupId=sg_id)
                continue

            logger.warning('Unknown client: %s', client)

        return ingress_resources

    def _app_sg(self, orbit, region, app, sg_ref='Sg'):
        cloudformation = self._clients.cloudformation(region)
        stack_name = '%s-%s' % (orbit.name, app)
        try:
            resource = cloudformation.describe_stack_resource(
                StackName=stack_name,
                LogicalResourceId=sg_ref)
            return (resource['StackResourceDetail']
                    ['PhysicalResourceId'])
        except ClientError as e:
            e_message = e.response['Error'].get('Message', '')
            if 'does not exist' in e_message:
                logger.debug('App %s not found in %s in %s.', app,
                             orbit.name, region)
                return None
            raise e

    def _app_eips(self, orbit, region, app):
        eips = []
        cloudformation = self._clients.cloudformation(region)
        stack_name = '%s-%s' % (orbit.name, app)
        try:
            p = cloudformation.get_paginator('list_stack_resources')
            for page in p.paginate(StackName=stack_name):
                for s in page['StackResourceSummaries']:
                    r = s['LogicalResourceId']
                    if r.startswith('ElasticIp') and not r.endswith('Policy'):
                        eips.append(s['PhysicalResourceId'])
            return eips
        except ClientError as e:
            e_message = e.response['Error'].get('Message', '')
            if 'does not exist' in e_message:
                return eips
            raise e
