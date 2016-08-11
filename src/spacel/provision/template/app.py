import base64
import json

from spacel.aws import INSTANCE_VOLUMES
from spacel.provision.template.base import BaseTemplateCache


class AppTemplate(BaseTemplateCache):
    def __init__(self, template_cache, ami_finder):
        super(AppTemplate, self).__init__(template_cache, ami_finder)

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
        self._subnet_params(params, 'PublicElb', public_elb_subnets)
        self._subnet_params(params, 'PrivateElb', private_elb_subnets)

        self._elb_subnets(resources, 'PublicElb', public_elb_subnets)
        self._elb_subnets(resources, 'PrivateElb', private_elb_subnets)

        # Expand ASG to all AZs:
        private_instance_subnets = orbit.private_instance_subnets(region)
        self._subnet_params(params, 'PrivateInstance', private_instance_subnets)
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
        # TODO: what about ranges? Can split `private_port`
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

    def _user_data(self, params, app):
        user_data = ''
        if app.services:
            systemd = {}
            files = {}
            for service_name, service in app.services.items():
                unit_file = service.unit_file.encode('utf-8')
                systemd[service.name] = {
                    'body': self._base64(unit_file)
                }
                if service.environment:
                    environment_file = '\n'.join('%s=%s' % (key, value)
                                                 for key, value in
                                                 service.environment.items())
                    files['%s.env' % service_name] = {
                        'body': self._base64(environment_file.encode('utf-8'))
                    }
            user_data += ',"systemd":' + json.dumps(systemd)
        if app.volumes:
            params['VolumeSupport']['Default'] = 'true'
            user_data += ', "volumes":' + json.dumps(app.volumes)
        return user_data

    @staticmethod
    def _base64(some_string):
        return base64.b64encode(some_string).decode('utf-8').strip()
