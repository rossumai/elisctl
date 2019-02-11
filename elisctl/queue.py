import json
from typing import Optional, IO

import click

from elisctl.lib.api_client import ELISClient, get_json
from elisctl.options import (
    bounce_email_option,
    connector_id_option,
    email_prefix_option,
    schema_content_file_option,
    workspace_id_option,
)


locale_option = click.option(
    "--locale",
    type=str,
    help="Document locale - passed to the Data Extractor, may influence e.g. date parsing.",
)


@click.group("queue")
def cli() -> None:
    pass


@cli.command(name="create", help="Create queue.")
@click.argument("name")
@email_prefix_option
@bounce_email_option
@schema_content_file_option
@workspace_id_option
@connector_id_option
@locale_option
def create_command(
    name: str,
    email_prefix: Optional[str],
    bounce_email: Optional[str],
    schema_content_file: Optional[IO[bytes]],
    workspace_id: Optional[int],
    connector_id: Optional[int],
    locale: Optional[str],
) -> None:
    schema_content = json.load(schema_content_file) if schema_content_file is not None else []
    with ELISClient() as elis:
        workspace_url = elis.get_workspace(workspace_id)["url"]
        connector_url = (
            get_json(elis.get(f"connectors/{connector_id}"))["url"]
            if connector_id is not None
            else None
        )

        schema_dict = elis.create_schema(f"{name} schema", schema_content)
        queue_dict = elis.create_queue(
            name, workspace_url, schema_dict["url"], connector_url, locale
        )

        inbox_dict = {"email": "no email-prefix specified"}
        if email_prefix is not None:
            inbox_dict = elis.create_inbox(
                f"{name} inbox", email_prefix, bounce_email, queue_dict["url"]
            )
    click.echo(f"{queue_dict['id']}, {inbox_dict['email']}")
