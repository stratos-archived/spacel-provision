from spacel.model.orbit import BASTION_INSTANCE_TYPE, BASTION_INSTANCE_COUNT
from spacel.provision.template.base import BaseTemplateCache


class BastionTemplate(BaseTemplateCache):
    def __init__(self, ami_finder):
        super(BastionTemplate, self).__init__(ami_finder=ami_finder)

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
        self._subnet_params(params, 'PublicInstance', instance_subnets)
        self._asg_subnets(resources, 'PublicInstance', instance_subnets)

        return bastion_template
