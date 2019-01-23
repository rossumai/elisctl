import click

from elisctl.user import create


@click.group("user")
def cli() -> None:
    pass


cli.add_command(create.create_command)
