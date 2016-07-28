import base64
from copy import deepcopy
import json
import logging
import os

from spacel.aws import AmiFinder, INSTANCE_VOLUMES
from spacel.model.orbit import (BASTION_INSTANCE_TYPE,
                                BASTION_INSTANCE_COUNT,
                                NAT_PER_AZ,
                                PRIVATE_NETWORK)

logger = logging.getLogger('spacel')


class TemplateCache(object):
    """
    Loads base templates from disk and tailors: to orbit, region, and/or
    application.
    """

    def __init__(self):
        self._cache = {}
        self._ami = AmiFinder()

    def get(self, template):
        """
        Load raw template.
        :param template: Template name.
        :return: JSON-decoded template.
        """
        cached = self._cache.get(template)
        if cached:
            return cached

        template_path = os.path.join('cloudformation', '%s.template' % template)
        with open(template_path) as template_in:
            loaded = json.loads(template_in.read())
            self._cache[template] = loaded
            return loaded

    def vpc(self, orbit, region):
        """
        Get customized template for VPC.
        :param orbit:  Orbit.
        :param region: Region.
        :return: VPC template.
        """
        vpc_template = self.get('vpc')
        params = vpc_template['Parameters']

        nat_per_az = orbit.get_param(region, NAT_PER_AZ)
        params['NatPerAz']['Default'] = nat_per_az and 'true' or 'false'

        params['VpcCidr']['Default'] = orbit.get_param(region, PRIVATE_NETWORK)

        azs = orbit.azs(region)
        if azs:
            resources = vpc_template['Resources']
            outputs = vpc_template['Outputs']

            base_az = params['Az01']
            base_az['Default'] = azs[0]

            base_nat_eip = resources['NatEip01']
            base_nat_gateway = resources['NatGateway01']
            base_default_route = resources['PrivateRouteTable01DefaultRoute']

            for index, az in enumerate(azs[1:]):
                az_index = (index + 2)
                az_param = 'Az%02d' % az_index

                # Each AZ should be declared as a parameter:
                params[az_param] = deepcopy(base_az)
                params[az_param]['Description'] = 'Generated AZ parameter.'
                params[az_param]['Default'] = az

                # Replicate route tables:
                rt_clone = deepcopy(resources['PrivateRouteTable01'])
                rt_name = self._get_name_tag(rt_clone['Properties'])
                rt_name['Fn::Join'][1][1] = 'Private%02d' % az_index
                private_rt_resource = 'PrivateRouteTable%02d' % az_index
                resources[private_rt_resource] = rt_clone

                # Replicate subnets:
                self._add_subnet(resources, outputs, az_index, az_param,
                                 'PublicInstance', az_index)
                self._add_subnet(resources, outputs, az_index, az_param,
                                 'PublicElb', 20 + az_index)
                nat_subnet_resource = self._add_subnet(resources, None,
                                                       az_index, az_param,
                                                       'PublicNat',
                                                       40 + az_index, )
                self._add_subnet(resources, outputs, az_index, az_param,
                                 'PrivateInstance', 100 + az_index,
                                 private_rt_resource)
                self._add_subnet(resources, outputs, az_index, az_param,
                                 'PrivateElb', 120 + az_index,
                                 private_rt_resource)

                # Each AZ _can_ have a NAT gateway:
                nat_eip_clone = deepcopy(base_nat_eip)
                nat_eip_clone['Condition'] = 'MultiAzNat'
                nat_eip_resource = 'NatEip%02d' % az_index
                resources[nat_eip_resource] = nat_eip_clone
                outputs[nat_eip_resource] = {
                    'Value': {'Fn::If': ['MultiAzNat',
                                         {'Ref': nat_eip_resource}, '']}
                }

                # Each AZ _can_ have a NAT gateway:
                nat_gateway_clone = deepcopy(base_nat_gateway)
                nat_gateway_clone['Condition'] = 'MultiAzNat'
                nat_gateway_props = nat_gateway_clone['Properties']
                nat_gateway_props['SubnetId']['Ref'] = nat_subnet_resource
                nat_gateway_props['AllocationId']['Fn::GetAtt'][0] = \
                    nat_eip_resource
                nat_gateway_resource = 'NatGateway%02d' % az_index
                resources[nat_gateway_resource] = nat_gateway_clone

                # Each private route table has a default NAT route:
                private_default_route_clone = deepcopy(base_default_route)
                private_route_props = private_default_route_clone['Properties']
                private_route_props['RouteTableId']['Ref'] = private_rt_resource
                private_route_props['NatGatewayId'] = {
                    'Fn::If': [
                        'MultiAzNat', {'Ref': nat_gateway_resource},
                        {'Ref': 'NatGateway01'}
                    ]
                }
                private_route_resource = 'PrivateRouteTable%02dDefaultRoute' % \
                                         az_index
                resources[private_route_resource] = private_default_route_clone

        return vpc_template

    def _add_subnet(self, resources, outputs, az_index, az, label, cidr,
                    rt=None):
        subnet_resource = '%sSubnet%02d' % (label, az_index)
        subnet_clone = deepcopy(resources['%sSubnet01' % label])
        subnet_props = subnet_clone['Properties']
        subnet_props['CidrBlock']['Fn::Join'][1][1] = '.%d.0/24' % cidr
        subnet_props['AvailabilityZone']['Ref'] = az
        subnet_name = self._get_name_tag(subnet_props)
        subnet_name['Fn::Join'][1][1] = '%s%02d' % (label, az_index)

        resources[subnet_resource] = subnet_clone
        if outputs:
            outputs[subnet_resource] = {
                'Value': {'Ref': subnet_resource}
            }

        base_rta = '%sSubnet01RouteTableAssociation' % label
        rta_clone = deepcopy(resources[base_rta])
        rta_props = rta_clone['Properties']
        rta_props['SubnetId']['Ref'] = subnet_resource
        if rt:
            rta_props['RouteTableId']['Ref'] = rt

        rta_resource = '%sSubnet%02dRouteTableAssociation' % (
            label, az_index)
        resources[rta_resource] = rta_clone
        return subnet_resource

    @staticmethod
    def _get_name_tag(resource_props):
        for tag in resource_props['Tags']:
            if tag['Key'] == 'Name':
                return tag['Value']
        return None

    def bastion(self, orbit, region):
        """
        Get customized template for bastion hosts.
        :param orbit: Orbit.
        :param region: Region.
        :return: Bastion template.
        """
        bastion_template = self.get('asg-bastion')

        params = bastion_template['Parameters']
        resources = bastion_template['Resources']

        # Link to VPC:
        params['VpcId']['Default'] = orbit.vpc_id(region)
        params['Orbit']['Default'] = orbit.name

        # Bastion parameters:
        bastion_type = orbit.get_param(region, BASTION_INSTANCE_TYPE)
        params['InstanceType']['Default'] = bastion_type
        params['Ami']['Default'] = self._ami.spacel_ami(region)

        bastion_count = int(orbit.get_param(region, BASTION_INSTANCE_COUNT))
        params['InstanceCount']['Default'] = bastion_count
        params['InstanceCountMinusOne']['Default'] = (bastion_count - 1)

        # TODO: support multiple sources (like ELB)

        # If multiple bastions, get more EIPs:
        if bastion_count > 1:
            eip_resource = resources['ElasticIp01']
            outputs = bastion_template['Outputs']

            eip_list = (resources['Lc']
                        ['Properties']
                        ['UserData']
                        ['Fn::Base64']
                        ['Fn::Join'][1][1]
                        ['Fn::Join'][1])

            for bastion_index in range(2, bastion_count + 1):
                eip_name = 'ElasticIp%02d' % bastion_index
                resources[eip_name] = eip_resource
                outputs[eip_name] = {'Value': {'Ref': eip_name}}
                eip_list.append({'Fn::GetAtt': [eip_name, 'AllocationId']})

        # Expand ASG to all AZs:
        instance_subnets = orbit.public_instance_subnets(region)
        self._subnet_params('PublicInstance', instance_subnets, params)
        self._asg_subnets(resources, 'PublicInstance', instance_subnets)

        return bastion_template

    def tables(self, orbit):
        """
        Get customized template for DynamoDb tables.
        :param orbit: Orbit.
        :return: DynamoDb tables.
        """

        tables_template = self.get('tables')
        params = tables_template['Parameters']
        params['Orbit']['Default'] = orbit.name
        return tables_template

    def app(self, app, region):
        app_template = self.get('elb-service')

        orbit = app.orbit
        params = app_template['Parameters']
        resources = app_template['Resources']

        # Link to VPC:
        params['VpcId']['Default'] = orbit.vpc_id(region)
        params['Orbit']['Default'] = orbit.name
        params['Service']['Default'] = app.name
        params['BastionSecurityGroup']['Default'] = orbit.bastion_sg(region)

        # Inject parameters:
        params['ElbScheme']['Default'] = app.scheme
        params['HealthCheckTarget']['Default'] = app.health_check
        params['InstanceType']['Default'] = app.instance_type
        params['InstanceMin']['Default'] = app.instance_min
        params['InstanceMax']['Default'] = app.instance_max
        params['UserData']['Default'] = self._user_data(params, app)
        params['Ami']['Default'] = self._ami.spacel_ami(region)

        if app.hostnames:
            # TODO: support multiple hostnames
            app_hostname = app.hostnames[0]
            domain = app_hostname.split('.')
            domain = '.'.join(domain[-2:]) + '.'
            params['VirtualHostDomain']['Default'] = domain
            params['VirtualHost']['Default'] = app_hostname
        else:
            params['VirtualHostDomain']['Default'] = orbit.domain + '.'
            generated_dns = '%s-%s.%s' % (app.name, orbit.name, orbit.domain)
            params['VirtualHost']['Default'] = generated_dns

        # Expand ELB to all AZs:
        public_elb_subnets = orbit.public_elb_subnets(region)
        private_elb_subnets = orbit.private_elb_subnets(region)
        self._subnet_params('PublicElb', public_elb_subnets, params)
        self._subnet_params('PrivateElb', private_elb_subnets, params)

        self._elb_subnets(resources, 'PublicElb', public_elb_subnets)
        self._elb_subnets(resources, 'PrivateElb', private_elb_subnets)

        # Expand ASG to all AZs:
        private_instance_subnets = orbit.private_instance_subnets(region)
        self._subnet_params('PrivateInstance', private_instance_subnets, params)
        self._asg_subnets(resources, 'PrivateInstance',
                          private_instance_subnets)

        # Public ports:
        elb_ingress = resources['ElbSg']['Properties']['SecurityGroupIngress']
        instance_ingress = resources['Sg']['Properties']['SecurityGroupIngress']
        public_elb = resources['PublicElb']['Properties']['Listeners']
        private_elb = resources['PrivateElb']['Properties']['Listeners']
        for port_number, port_config in app.public_ports.items():
            # Allow all sources into ELB:
            for ip_source in port_config.sources:
                elb_ingress.append({
                    'IpProtocol': 'tcp',
                    'FromPort': port_number,
                    'ToPort': port_number,
                    'CidrIp': ip_source
                })

            # Allow ELB->Instance
            instance_ingress.append({
                'IpProtocol': 'tcp',
                'FromPort': port_number,
                'ToPort': port_number,
                'SourceSecurityGroupId': {'Ref': 'ElbSg'}
            })

            elb_listener = {
                'InstancePort': port_number,
                'LoadBalancerPort': port_number,
                'Protocol': port_config.scheme,
                'InstanceProtocol': port_config.internal_scheme
            }
            public_elb.append(elb_listener)
            private_elb.append(elb_listener)

        # Private ports:
        for private_port, protocols in app.private_ports.items():
            for protocol in protocols:
                port_resource = 'PrivatePort%s%s' % (private_port, protocol)
                resources[port_resource] = {
                    'Type': 'AWS::EC2::SecurityGroupIngress',
                    'Properties': {
                        'GroupId': {'Ref': 'Sg'},
                        'IpProtocol': protocol,
                        'FromPort': private_port,
                        'ToPort': private_port,
                        'SourceSecurityGroupId': {'Ref': 'Sg'}
                    }
                }

        # Map instance storage if available:
        instance_volumes = INSTANCE_VOLUMES.get(app.instance_type, 0)
        if instance_volumes > 0:
            block_devices = resources['Lc']['Properties']['BlockDeviceMappings']
            for volume_index in range(instance_volumes):
                device = '/dev/xvd%s' % chr((ord('b') + volume_index))
                block_devices.append({
                    'DeviceName': device,
                    'VirtualName': 'ephemeral%d' % volume_index
                })

        return app_template

    @staticmethod
    def _user_data(params, app):
        user_data = ''
        if app.services:
            systemd = {}
            files = {}
            for service_name, service in app.services.items():
                unit_file = service.unit_file.encode('utf-8')
                systemd[service.name] = {
                    'body': TemplateCache._base64(unit_file)
                }
                if service.environment:
                    environment_file = '\n'.join('%s=%s' % (key, value)
                                                 for key, value in
                                                 service.environment.items())
                    files['%s.env' % service_name] = {
                        'body': TemplateCache._base64(environment_file)
                    }
            user_data += ',"systemd":' + json.dumps(systemd)
        if app.volumes:
            params['VolumeSupport']['Default'] = 'true'
            user_data += ', "volumes":' + json.dumps(app.volumes)
        return user_data

    @staticmethod
    def _base64(some_string):
        return base64.b64encode(some_string).decode('utf-8').strip()

    @staticmethod
    def _services(app):
        if not app.services:
            return None

        systemd = {}
        for service_name, service in app.services.items():
            uf_bytes = service.unit_file.encode('utf-8')
            unit_file = base64.b64encode(uf_bytes).decode('utf-8').strip()
            systemd[service.name] = {
                'body': unit_file
            }

        return '\"systemd\":%s' % json.dumps(systemd)

    @staticmethod
    def _asg_subnets(resources, subnet_type, instance_subnets):
        asg_subnets = resources['Asg']['Properties']['VPCZoneIdentifier']
        for index, subnet in enumerate(instance_subnets[1:]):
            subnet_param = '%sSubnet%02d' % (subnet_type, index + 2)
            asg_subnets.append({'Ref': subnet_param})

    @staticmethod
    def _elb_subnets(resources, elb_type, subnets):
        elb_subnets = resources[elb_type]['Properties']['Subnets']
        for index, subnet in enumerate(subnets[1:]):
            subnet_param = '%sSubnet%02d' % (elb_type, index + 2)
            elb_subnets.append({"Ref": subnet_param})

    @staticmethod
    def _subnet_params(subnet_type, subnets, params):
        base_subnet = params['%sSubnet01' % subnet_type]
        base_subnet['Default'] = subnets[0]
        for index, subnet in enumerate(subnets[1:]):
            az_index = (index + 2)
            subnet_param = '%sSubnet%02d' % (subnet_type, az_index)

            # Each AZ should be declared as a parameter:
            params[subnet_param] = deepcopy(base_subnet)
            params[subnet_param]['Description'] = 'Generated subnet parameter.'
            params[subnet_param]['Default'] = subnet
