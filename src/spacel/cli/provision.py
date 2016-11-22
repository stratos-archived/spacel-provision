import click


@click.group()
def provision_cmd():  # pragma: no cover
    pass


@provision_cmd.command(help='Provision/upgrade resources for deployment.')
def provision():  # pragma: no cover
    provision_services()


def provision_services():
    print('provision')
