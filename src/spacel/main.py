#!/usr/bin/env python

import logging
import sys

from colorlog import ColoredFormatter


def setup_logging(level=logging.DEBUG):
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            return

    if level > logging.DEBUG:
        date_format = '%Y-%m-%d %H:%M:%S'
    else:
        date_format = None

    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(message)s",
        datefmt=date_format,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red'
        }
    )
    stream_out = logging.StreamHandler()
    stream_out.setLevel(level)
    stream_out.setFormatter(formatter)
    root_logger.addHandler(stream_out)
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('paramiko').setLevel(logging.CRITICAL)
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.getLogger('tldextract').setLevel(logging.CRITICAL)
    logging.getLogger('spacel').setLevel(logging.DEBUG)


def legacy_args(args):
    # Legacy support: map 2 simple args to `provision` subcommand
    if len(args) == 2:
        no_dash = [arg for arg in args if not arg.startswith('--')]
        if len(no_dash) == 2:
            args.insert(0, 'provision')
            args.insert(1, '--orbit')
            args.insert(3, '--app')


if __name__ == '__main__':  # pragma: no cover
    from spacel.cli import cli

    legacy_args(sys.argv)
    cli()
