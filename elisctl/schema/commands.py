import json

from typing import Optional, IO

import click

from elisctl import option
from elisctl.lib.api_client import APIClient, get_json
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
@click.argument("id_", metavar="ID", type=str)
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
