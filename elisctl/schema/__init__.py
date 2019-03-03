import json
from typing import IO, Optional

import click

from elisctl.lib.api_client import APIClient, get_json

from . import transform, upload


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
@click.option("-O", "--output-file", type=click.File("w", encoding="utf-8"))
def download_command(
    ctx: click.Context, id_: str, indent: int, ensure_ascii: bool, output_file: Optional[IO[str]]
):
    with APIClient() as api_client:
        schema_dict = get_json(api_client.get(f"schemas/{id_}"))
    schema_json = json.dumps(
        schema_dict["content"], indent=indent, ensure_ascii=ensure_ascii, sort_keys=True
    )
    click.echo(schema_json, file=output_file)
