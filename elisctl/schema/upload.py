#!/usr/bin/env python3
import json
from typing import List, Optional, Dict, Union

import click as click
from typing.io import IO

from elisctl.lib.api_client import get_json, ELISClient


SchemaContent = List[dict]
Schema = Dict[str, Union[str, SchemaContent]]


@click.command(name="update")
@click.argument("id_", metavar="ID", type=str)
@click.argument("json_file", metavar="JSON", type=click.File("r"))
@click.option("--rewrite", is_flag=True, type=bool)
@click.option("--name", default=None, type=str)
def upload_command(id_: str, json_file: IO[str], rewrite: bool, name: Optional[str]):
    """
    Update schema in ELIS.
    """
    func = _rewrite_schema if rewrite else _create_schema
    with ELISClient() as elis:
        func(id_, json.load(json_file), elis, name)


def _rewrite_schema(
    id_: str, schema_content: SchemaContent, elis: ELISClient, name: Optional[str]
) -> None:
    data: Schema = {"content": schema_content}
    if name is not None:
        data["name"] = name
    elis.patch(f"schemas/{id_}", data=data)


def _create_schema(
    id_: str, schema_content: SchemaContent, elis: ELISClient, name: Optional[str]
) -> None:
    original_schema = get_json(elis.get(f"schemas/{id_}"))
    new_schema = elis.create_schema(name or original_schema["name"], schema_content)

    for queue_url in original_schema["queues"]:
        if queue_url.startswith(elis.url):
            queue_url = queue_url[len(elis.url) + 1 :]
        elis.patch(queue_url, data={"schema": new_schema["url"]})
