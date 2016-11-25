import json

from test import BaseSpaceAppTest
from test.provision import normalize_cf


class BaseTemplateDecoratorTest(BaseSpaceAppTest):
    def setUp(self):
        super(BaseTemplateDecoratorTest, self).setUp()
        self.user_data_params = []
        self.resources = {
            'Lc': {
                'Properties': {
                    'UserData': {
                        'Fn::Base64': {
                            'Fn::Join': [
                                '', self.user_data_params
                            ]
                        }
                    }
                }
            }
        }
        self.parameters = {}
        self.template = {
            'Parameters': self.parameters,
            'Resources': self.resources
        }

    def _user_data(self):
        user_data_params = normalize_cf(self.user_data_params)
        user_data_text = ''.join(user_data_params)
        try:
            return json.loads(user_data_text)
        except ValueError:
            return user_data_text
