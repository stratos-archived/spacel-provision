import logging
import re

from botocore.exceptions import ClientError

from spacel.provision import clean_name

IP_BLOCK = re.compile('(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}/\d{1,3})')
logger = logging.getLogger('spacel.provision.ingress_resource')

# See: INSTANCE_AVAILABILITY and ELB_AVAILABILITY in SpaceAppRegion.
AVAILABILITY_NOT_PUBLIC = {
    'multi-region',
    'private'
}


class IngressResourceFactory(object):
    def __init__(self, clients):
        self._clients = clients

    def ingress_resources(self, app_region, start_port, clients,
                          protocol='TCP', end_port=None, sg_ref='Sg',
                          availability=None):
        """
        Return ingress resources for access from a list of clients.
        :param app_region:  AppRegion.
        :param start_port: First port to open
        :param clients: Client list.
        :param protocol: Protocol.
        :param end_port: Last port to open (defaults to start_port if not set).
        :param sg_ref: Security group name.
        :param availability: Resource availability.
        :return: dict of {resource_name: cloudformation_resource}
        """
        # Parameter normalization:
        orbit = app_region.orbit_region.orbit
        region = app_region.orbit_region.region
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
            ip_match = IP_BLOCK.match(client)
            if ip_match:
                rfc1918 = self._is_rfc1918(ip_match)
                if not rfc1918 and availability in AVAILABILITY_NOT_PUBLIC:
                    logger.warning('Ignoring IP %s for %s service.', client,
                                   availability)
                    continue

                logger.debug('Adding access from %s.', client)
                ingress_resource(client, CidrIp=client)
                continue

            # This orbit region:
            if client == region:
                network = '%s.0.0/16' % orbit.regions[region].private_network
                ingress_resource('Orbit%s' % client, CidrIp=network)
                continue

            # Another orbit region (NAT-ed instances in that region):
            if client in orbit.regions:
                logger.debug('Adding access from %s in %s.', orbit.name, client)
                orbit_region = orbit.regions[client]

                eips = self._app_eips(orbit_region, client)
                if eips:
                    for eip_index, eip in enumerate(eips):
                        eip_index += 1
                        if eip:
                            ingress_resource('ElasticIp%s%s' % (client,
                                                                eip_index),
                                             CidrIp='%s/32' % eip)
                else:
                    for az, orbit_az in orbit_region.azs.items():
                        if orbit_az.nat_eip:
                            ingress_resource('Nat%s%s' % (client, az),
                                             CidrIp='%s/32' % orbit_az.nat_eip)
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

    def _app_eips(self, orbit_region, app):
        eips = []
        cloudformation = self._clients.cloudformation(orbit_region.region)
        stack_name = '%s-%s' % (orbit_region.orbit.name, app)
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

    @staticmethod
    def _is_rfc1918(ip_match):
        first_octet = ip_match.group(1)
        if first_octet == '10':
            return True
        if first_octet == '172':
            return 16 <= int(ip_match.group(2)) < 32
        if first_octet == '192':
            return ip_match.group(2) == '168'
        return False
