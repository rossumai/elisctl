import click

from tools.user import create


@click.group("user")
def cli() -> None:
    pass


cli.add_command(create.create_command)
