from copy import deepcopy
import json
import os


class BaseTemplateCache(object):
    """
    Loads base templates from disk and tailors: to orbit, region, and/or
    application.
    """

    def __init__(self, ami_finder=None):
        self._cache = {}
        self._ami = ami_finder

    def get(self, template):
        """
        Load raw template.
        :param template: Template name.
        :return: JSON-decoded template.
        """
        cached = self._cache.get(template)
        if cached:
            return deepcopy(cached)

        template_path = os.path.join('cloudformation', '%s.template' % template)
        with open(template_path) as template_in:
            loaded = json.loads(template_in.read())
            self._cache[template] = loaded
            return deepcopy(loaded)

    @staticmethod
    def _get_name_tag(resource_props):
        for tag in resource_props['Tags']:
            if tag['Key'] == 'Name':
                return tag['Value']
        return None

    @staticmethod
    def _subnet_params(params, subnet_type, subnets):
        """
        Replicate subnet parameters.
        :param params: CloudFormation template "Parameters" section.
        :param subnet_type: Subnet type (i.e. PublicELB, PrivateInstance).
        :param subnets: Subnet IDs.
        """
        base_subnet = params['%sSubnet01' % subnet_type]
        base_subnet['Default'] = subnets[0]
        for index, subnet in enumerate(subnets[1:]):
            az_index = (index + 2)
            subnet_param = '%sSubnet%02d' % (subnet_type, az_index)

            # Each AZ should be declared as a parameter:
            params[subnet_param] = deepcopy(base_subnet)
            params[subnet_param]['Description'] = 'Generated subnet parameter.'
            params[subnet_param]['Default'] = subnet

    @staticmethod
    def _asg_subnets(resources, subnet_type, instance_subnets):
        """
        Replicate subnet parameters in an ASG.
        :param resources: CloudFormation template "Resources" section.
        :param subnet_type: Subnet type (i.e. PublicInstance, PrivateInstance).
        :param instance_subnets: Subnet IDs
        """
        asg_subnets = resources['Asg']['Properties']['VPCZoneIdentifier']
        for index, subnet in enumerate(instance_subnets[1:]):
            subnet_param = '%sSubnet%02d' % (subnet_type, index + 2)
            asg_subnets.append({'Ref': subnet_param})

    @staticmethod
    def _elb_subnets(resources, elb_type, subnets):
        """
        Replicate subnet parameters in an ELB.
        :param resources: CloudFormation template "Resources" section.
        :param elb_type: ELB type (i.e. PublicELB, PrivateELB).
        :param subnets: Subnet IDs.
        """
        elb_subnets = resources[elb_type]['Properties']['Subnets']
        for index, subnet in enumerate(subnets[1:]):
            subnet_param = '%sSubnet%02d' % (elb_type, index + 2)
            elb_subnets.append({"Ref": subnet_param})
