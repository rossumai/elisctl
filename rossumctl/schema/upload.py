#!/usr/bin/env python3
import click as click
from typing import List, Optional, Dict, Union, Callable
from typing.io import IO

from rossumctl import argument
from rossumctl.lib.api_client import get_json, RossumClient

SchemaContent = List[dict]
Schema = Dict[str, Union[str, SchemaContent]]
LoadFunction = Callable[[IO[bytes]], SchemaContent]


@click.command(name="update")
@argument.id_(type=str)
@argument.schema_content
@click.option("--rewrite", is_flag=True, type=bool)
@click.option("--name", default=None, type=str)
@click.pass_context
def upload_command(
    ctx: click.Context, id_: str, schema_content: List[dict], rewrite: bool, name: Optional[str]
):
    """
    Update schema in ROSSUM.
    """
    upload_func = _rewrite_schema if rewrite else _create_schema
    with RossumClient(context=ctx.obj) as rossum:
        upload_func(id_, schema_content, rossum, name)


def _rewrite_schema(
    id_: str, schema_content: SchemaContent, rossum: RossumClient, name: Optional[str]
) -> None:
    data: Schema = {"content": schema_content}
    if name is not None:
        data["name"] = name
    rossum.patch(f"schemas/{id_}", data=data)


def _create_schema(
    id_: str, schema_content: SchemaContent, rossum: RossumClient, name: Optional[str]
) -> None:
    original_schema = get_json(rossum.get(f"schemas/{id_}"))
    new_schema = rossum.create_schema(name or original_schema["name"], schema_content)

    for queue_url in original_schema["queues"]:
        if queue_url.startswith(rossum.url):
            queue_url = queue_url[len(rossum.url) + 1 :]
        rossum.patch(queue_url, data={"schema": new_schema["url"]})
