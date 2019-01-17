import click

from tools import tools, schema, csv


@click.group("elisctl", context_settings={"help_option_names": ["-h", "--help"]})
def entry_point() -> None:
    pass


entry_point.add_command(tools.cli)
entry_point.add_command(csv.cli)
entry_point.add_command(schema.cli)
