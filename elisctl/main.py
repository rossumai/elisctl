import click
from click_shell import shell

from elisctl import tools, schema, csv, configure, user, workspace, queue, __version__


@shell(
    prompt="elis> ",
    intro="Welcome to the elisctl interactive mode. Start with `help` and `configure`.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__)
def entry_point() -> None:
    pass


entry_point.add_command(tools.cli)
entry_point.add_command(csv.cli)
entry_point.add_command(schema.cli)
entry_point.add_command(user.cli)
entry_point.add_command(workspace.cli)
entry_point.add_command(queue.cli)
entry_point.add_command(configure.cli)
