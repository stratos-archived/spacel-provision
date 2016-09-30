from argparse import ArgumentParser
import json
import logging
import os
import sys

import boto3
import six
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import urlparse
from six.moves.urllib.request import urlopen
from splitstream import splitfile

logger = logging.getLogger('spacel')


class ErrorEatingArgumentParser(ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)


PARSER = ErrorEatingArgumentParser(prog='spacel.main',
                                   description='Spacel provisioner')
PARSER.add_argument('orbit_url')
PARSER.add_argument('app_url')


def parse_args(args, in_stream):
    parsed = PARSER.parse_args(args)
    if not parsed.orbit_url or not parsed.app_url:
        return None, None

    if in_stream.isatty():
        in_split = iter(())
    else:
        in_split = splitfile(in_stream, format='json')

    orbit = read_manifest(parsed.orbit_url, 'orbit_url', in_split)
    app = read_manifest(parsed.app_url, 'app_url', in_split)
    return orbit, app


def parse_s3(s3_url):
    key = s3_url.path[1:]

    hostname = s3_url.hostname
    aws_pos = hostname.find('.amazonaws.com')
    if aws_pos != -1:
        host_prefix = hostname[:aws_pos]
        if '.' in host_prefix:
            bucket, host_prefix = host_prefix.split('.', 1)
        else:
            _, bucket, key = s3_url.path.split('/', 2)
        region = host_prefix.replace('s3.', '').replace('s3-', '')
    else:
        region = 'us-east-1'
        bucket = hostname

    return region, bucket, key


def read_manifest(name, label, in_split):
    url = urlparse(name)
    if url.scheme in ('http', 'https'):
        try:
            opened = urlopen(name)
            json_body = opened.read()
        except HTTPError as e:
            logger.warning('Unable to read manifest from %s: %s - %s', name,
                           e.code,
                           e.msg)
            return None
    elif url.scheme == 's3':
        region, bucket, key = parse_s3(url)
        s3_resource = boto3.resource('s3', region)
        json_body = s3_resource.Object(bucket, key).get()['Body'].read()
    elif not url.scheme and url.path == '-':
        try:
            json_body = six.next(in_split)
        except StopIteration:
            logger.warning('Unable to read %s manifest from stdin.', label)
            return None
    elif os.path.isfile(name):
        with open(name, 'rb') as file_in:
            json_body = file_in.read()
    else:
        logger.warning('Invalid input URL for %s: %s', label, name)
        return None

    if json_body:
        return json.loads(json_body.decode('utf-8'))
