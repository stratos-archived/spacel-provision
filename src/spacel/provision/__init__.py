import base64
import re

import six


def clean_name(name):
    return re.sub('[^A-Za-z0-9]', '', name)


def bool_param(params, name, default):
    val = params.get(name)
    if val is None:
        return default
    return bool(val)


def base64_encode(some_data):
    if isinstance(some_data, six.string_types):
        some_data = some_data.encode('utf-8')

    return base64.b64encode(some_data).decode('utf-8').strip()


def base64_decode(some_string):
    return base64.b64decode(some_string)


from .app import SpaceElevatorAppFactory
from .changesets import ChangeSetEstimator
from .orbit import ProviderOrbitFactory
from .s3 import LambdaUploader, TemplateUploader
