import click

from elisctl import tools, schema, csv, configure, user


@click.group("elisctl", context_settings={"help_option_names": ["-h", "--help"]})
def entry_point() -> None:
    pass


entry_point.add_command(tools.cli)
entry_point.add_command(csv.cli)
entry_point.add_command(schema.cli)
entry_point.add_command(user.cli)
entry_point.add_command(configure.cli)
