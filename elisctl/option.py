from typing import Optional, Callable

import click

organization = click.option(
    "-o", "--organization-id", type=int, help="Organization ID.", hidden=True
)

name = click.option("-n", "--name", type=str)
email_prefix = click.option(
    "--email-prefix", type=str, help="If not specified, documents cannot be imported via email."
)
bounce_email = click.option(
    "--bounce-email", type=str, help="Unprocessable documents will be bounced to this email."
)
connector_id = click.option(
    "--connector-id", type=str, help="If not specified, queue will not call back a connector."
)

output_file = click.option("-O", "--output-file", type=click.File("wb"))


def schema_content_file(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": click.File("rb"), "help": "Schema JSON file."}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-s", "--schema-content-file", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def workspace_id(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": int, "help": "Workspace ID."}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-w", "--workspace-id", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


queue = click.option(
    "-q",
    "--queue-id",
    "queue_ids",
    type=int,
    multiple=True,
    help="Queue IDs, which the user will be associated with.",
)


def group(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {
        "default": "annotator",
        "type": click.Choice(["annotator", "admin", "viewer"]),
        "help": "Permission group.",
        "show_default": True,
    }
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-g", "--group", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def locale(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {
        "default": "en",
        "type": click.Choice(["en", "cs"]),
        "help": "UI locale",
        "show_default": True,
    }
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-l", "--locale", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def password(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": str, "required": False, "help": "Generated, if not specified."}
    kwargs = {**default_kwargs, **kwargs}
    if "help" in kwargs and kwargs["help"] is None:
        kwargs.pop("help")
    decorator = click.option("-p", "--password", **kwargs)
    if command is None:
        return decorator
    return decorator(command)
