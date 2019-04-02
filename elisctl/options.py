from typing import Optional, Callable

import click

organization_option = click.option(
    "-o", "--organization-id", type=int, help="Organization ID.", hidden=True
)

name_option = click.option("-n", "--name", type=str)
email_prefix_option = click.option(
    "--email-prefix", type=str, help="If not specified, documents cannot be imported via email."
)
bounce_email_option = click.option(
    "--bounce-email", type=str, help="Unprocessable documents will be bounced to this email."
)
connector_id_option = click.option(
    "--connector-id", type=str, help="If not specified, queue will not call back a connector."
)

output_file_option = click.option("-O", "--output-file", type=click.File("wb"))


def schema_content_file_option(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": click.File("rb"), "help": "Schema JSON file."}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-s", "--schema-content-file", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def workspace_id_option(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": int, "help": "Workspace ID."}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-w", "--workspace-id", **kwargs)
    if command is None:
        return decorator
    return decorator(command)
