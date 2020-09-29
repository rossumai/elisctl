import click
from click_shell import shell

import elisctl.schema.commands
from elisctl import (
    tools,
    configure,
    user,
    workspace,
    queue,
    connector,
    hook,
    document,
    __version__,
    CTX_DEFAULT_PROFILE,
    CTX_PROFILE,
    user_assignment,
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
entry_point.add_command(elisctl.schema.commands.cli)
entry_point.add_command(user.cli)
entry_point.add_command(user_assignment.cli)
entry_point.add_command(workspace.cli)
entry_point.add_command(queue.cli)
entry_point.add_command(document.cli)
entry_point.add_command(connector.cli)
entry_point.add_command(hook.cli)
entry_point.add_command(configure.cli)
