import functools
import json
from typing import IO, Optional, Callable, Iterable

import click

from elisctl.common import schema_content_factory
from elisctl.lib import split_dict_params

name = click.argument("name", type=str)


def id_(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": int, "metavar": "ID"}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.argument("id_", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def schema_file(command: Callable):
    click.argument("schema_file", type=click.File("rb"))(command)

    @functools.wraps(command)
    def wrapped(ctx: click.Context, schema_file: IO[str], *args, **kwargs):
        ctx.obj = {"SCHEMA": json.load(schema_file)}
        return command(ctx, *args, **kwargs)

    return wrapped


def datapoint_parameters(command: Callable):
    click.argument("datapoint_parameters", nargs=-1, type=str)(command)

    @functools.wraps(command)
    def wrapped(*args, datapoint_parameters: Iterable[str], **kwargs):
        try:
            split_params = split_dict_params(datapoint_parameters)
        except ValueError as e:
            raise click.BadArgumentUsage("Expecting <key>=<value> pairs.") from e
        return command(*args, datapoint_parameters=dict(split_params), **kwargs)

    return wrapped


def schema_content_file(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": click.File("rb"), "metavar": "FILE"}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.argument("schema_content_file_", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


schema_content = schema_content_factory(schema_content_file)
