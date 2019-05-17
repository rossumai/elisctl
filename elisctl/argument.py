import functools
import json
from typing import IO, Optional, Callable

import click

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
