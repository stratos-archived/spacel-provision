import click
from .provision import provision_cmd
from .secret import secret_cmd

commands = (provision_cmd, secret_cmd)
cli = click.CommandCollection(sources=commands)
