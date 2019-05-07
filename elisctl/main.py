import click
from click_shell import shell

from elisctl import (
    tools,
    schema,
    csv,
    configure,
    user,
    workspace,
    queue,
    __version__,
    CTX_DEFAULT_PROFILE,
    CTX_PROFILE,
)


@shell(
    prompt="elis> ",
    intro="Welcome to the elisctl interactive mode. Start with `help` and `configure`.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__)
@click.option(
    "-p",
    "--profile",
    default=CTX_DEFAULT_PROFILE,
    type=str,
    help="Profile name.",
    show_default=True,
)
@click.pass_context
def entry_point(ctx: click.Context, profile: str) -> None:
    ctx.obj = {CTX_PROFILE: profile}


entry_point.add_command(tools.cli)
entry_point.add_command(csv.cli)
entry_point.add_command(schema.cli)
entry_point.add_command(user.cli)
entry_point.add_command(workspace.cli)
entry_point.add_command(queue.cli)
entry_point.add_command(configure.cli)
