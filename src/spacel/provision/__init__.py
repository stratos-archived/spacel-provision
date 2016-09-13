import re

from .changesets import ChangeSetEstimator
from .s3.lambda_uploader import LambdaUploader
from .orbit import ProviderOrbitFactory
from .provision import CloudProvisioner


def clean_name(name):
    return re.sub('[^A-Za-z0-9]', '', name)