import json

from typing import Optional, IO

import click
from tabulate import tabulate

from elisctl import option, argument
from elisctl.lib.api_client import APIClient, get_json, ELISClient
from elisctl.lib import QUEUES

from . import upload
from .xlsx import SchemaToXlsx
from .transform import commands as transform


@click.group("schema")
def cli() -> None:
    pass


cli.add_command(transform.cli)
cli.add_command(upload.upload_command)


@cli.command(name="get", help="Download schema from ELIS.")
@click.pass_context
@argument.id_(type=str)
@click.option("--indent", default=2, type=int)
@click.option("--ensure-ascii", is_flag=True, type=bool)
@click.option("--format", "format_", default="json", type=click.Choice(["json", "xlsx"]))
@option.output_file
def download_command(
    ctx: click.Context,
    id_: str,
    indent: int,
    ensure_ascii: bool,
    format_: str,
    output_file: Optional[IO[str]],
):
    with APIClient(context=ctx.obj) as api_client:
        schema_dict = get_json(api_client.get(f"schemas/{id_}"))
    if format_ == "json":
        schema_file = json.dumps(
            schema_dict["content"], indent=indent, ensure_ascii=ensure_ascii, sort_keys=True
        ).encode("utf-8")
    else:
        schema_file = SchemaToXlsx().convert(schema_dict["content"])

    click.echo(schema_file, file=output_file, nl=False)


@cli.command(name="list", help="List all schemas.")
@click.pass_context
def list_command(ctx: click.Context,):
    with ELISClient(context=ctx.obj) as elis:
        schemas = elis.get_schemas((QUEUES,))

    table = [
        [schema["id"], schema["name"], ", ".join(str(s.get("id", "")) for s in schema["queues"])]
        for schema in schemas
    ]

    click.echo(tabulate(table, headers=["id", "name", "queues"]))
