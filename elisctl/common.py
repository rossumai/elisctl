import json
import functools
from typing import Optional, Callable, IO, List

import click

from elisctl.schema.xlsx import XlsxToSchema

file_format = click.option(
    "--format", "format_", default="json", type=click.Choice(["json", "xlsx"])
)


def schema_content_factory(file_decorator):
    def schema_content(command: Optional[Callable] = None, **file_decorator_kwargs):
        def _load_func(format_: str) -> Callable[[IO[bytes]], List[dict]]:
            if format_ == "json":
                return json.load
            elif format_ == "xlsx":
                return XlsxToSchema().convert
            else:
                raise NotImplementedError

        def decorator(command_: Callable):
            @file_decorator(**file_decorator_kwargs)
            @file_format
            @functools.wraps(command_)
            def wrapped(*args, schema_content_file_: Optional[IO[bytes]], format_: str, **kwargs):
                if schema_content_file_ is None:
                    return command_(*args, schema_content=None, **kwargs)
                try:
                    schema_content = _load_func(format_)(schema_content_file_)
                except Exception as e:
                    raise click.ClickException(
                        f"File {schema_content_file_} could not be loaded. Because of {e}"
                    ) from e

                return command_(*args, schema_content=schema_content, **kwargs)

            return wrapped

        if command is None:
            return decorator
        return decorator(command)

    return schema_content
