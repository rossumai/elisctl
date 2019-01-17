#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import List, Optional, Dict, Union

import click as click
from typing.io import IO

from tools.lib.api_client import APIClient, get_json

HELP = """\
Update schema in ELIS.

WARNING: creation of schema must be carried out with a user from within the organization.
The reason is that the schema is automatically attached to the organization of the user,
who is creating it.
"""


@click.command(name="update", help=HELP)
@click.argument("id_", metavar="ID", type=str)
@click.argument("json_file", metavar="JSON", type=click.File("rb"))
@click.option("--rewrite", is_flag=True, type=bool)
@click.option("--name", default=None, type=str)
def upload_command(id_: str, json_file: IO[bytes], rewrite: bool, name: Optional[str]):
    func = _rewrite_schema if rewrite else _create_schema
    with APIClient() as api_client:
        func(id_, json.load(json_file), api_client, name)


def _rewrite_schema(
    id_: str,
    schema_content: SchemaContent,  # noqa: F821
    api_client: APIClient,
    name: Optional[str],
) -> None:
    data: Schema = {"content": schema_content}
    if name is not None:
        data["name"] = name
    api_client.patch(f"schemas/{id_}", data=data)


def _create_schema(
    id_: str,
    schema_content: SchemaContent,  # noqa: F821
    api_client: APIClient,
    name: Optional[str],
) -> None:
    original_schema = get_json(api_client.get(f"schemas/{id_}"))
    new_schema = get_json(
        api_client.post(
            "schemas", data={"name": name or original_schema["name"], "content": schema_content}
        )
    )
    for queue_url in original_schema["queues"]:
        if queue_url.startswith(api_client.url):
            queue_url = queue_url[len(api_client.url) + 1 :]
        api_client.patch(queue_url, data={"schema": new_schema["url"]})


SchemaContent = List[dict]
Schema = Dict[str, Union[str, SchemaContent]]
