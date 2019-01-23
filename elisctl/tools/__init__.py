import click

from . import csv_to_options, xls_to_csv, compare


@click.group("tools")
def cli() -> None:
    pass


cli.add_command(compare.cli)
cli.add_command(csv_to_options.cli)
cli.add_command(xls_to_csv.cli)
