import click

from . import extract_data


@click.group("document")
def cli() -> None:
    pass


cli.add_command(extract_data.get_data)
