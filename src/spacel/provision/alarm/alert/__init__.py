import re


def clean_name(name):
    return re.sub('[^A-Za-z0-9]', '', name)
