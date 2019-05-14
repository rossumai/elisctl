import json

import functools

import click
from typing import IO

id_ = click.argument("id_", metavar="ID", type=int)


def schema_file(command):
    click.argument("schema_file", type=click.File("rb"))(command)

    @functools.wraps(command)
    def wrapped(ctx: click.Context, schema_file: IO[str], *args, **kwargs):
        ctx.obj = {"SCHEMA": json.load(schema_file)}
        return command(ctx, *args, **kwargs)

    return wrapped
