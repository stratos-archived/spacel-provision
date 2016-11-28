class BaseTemplateDecorator(object):
    @staticmethod
    def _user_data(resources):
        return (resources['Lc']
                ['Properties']
                ['UserData']
                ['Fn::Base64']
                ['Fn::Join'][1])
