import click
from click_shell import shell

from elisctl import tools, schema, csv, configure, user


@shell(
    prompt="elis> ",
    intro="Welcome to the elisctl interactive mode. Start with `help` and `configure`.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option()
def entry_point() -> None:
    pass


entry_point.add_command(tools.cli)
entry_point.add_command(csv.cli)
entry_point.add_command(schema.cli)
entry_point.add_command(user.cli)
entry_point.add_command(configure.cli)
