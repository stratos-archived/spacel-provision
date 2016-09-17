import re

from .changesets import ChangeSetEstimator
from .orbit import ProviderOrbitFactory
from .provision import CloudProvisioner
from .s3 import LambdaUploader, TemplateUploader


def clean_name(name):
    return re.sub('[^A-Za-z0-9]', '', name)


def bool_param(params, name, default):
    val = params.get(name)
    if val is None:
        return default
    return bool(val)
