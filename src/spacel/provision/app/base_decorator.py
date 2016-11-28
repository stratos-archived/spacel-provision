class BaseTemplateDecorator(object):
    """
    Shared functionality to modify an existing CloudFormation template.
    """

    @staticmethod
    def _lc_user_data(resources):
        """
        Get the UserData component from template's LaunchConfiguration.
        :param resources:  Template resources.
        :return: List of strings to be joined as user data.
        """
        return (resources['Lc']
                ['Properties']
                ['UserData']
                ['Fn::Base64']
                ['Fn::Join'][1])
