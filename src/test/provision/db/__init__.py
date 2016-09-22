import json
from mock import MagicMock

from spacel.provision.template import IngressResourceFactory

from test import BaseSpaceAppTest
from test.provision import normalize_cf


class BaseDbTest(BaseSpaceAppTest):
    def setUp(self):
        super(BaseDbTest, self).setUp()
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

        self.ingress = MagicMock(spec=IngressResourceFactory)

    def _user_data(self):
        user_data_params = normalize_cf(self.user_data_params)
        user_data = json.loads(''.join(user_data_params))
        return user_data
