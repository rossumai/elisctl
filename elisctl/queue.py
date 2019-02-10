import json
from typing import Optional, IO

import click

from elisctl.lib.api_client import ELISClient
from elisctl.options import (
    email_prefix_option,
    schema_content_file_option,
    workspace_id_option,
    bounce_email_option,
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
def create_command(
    name: str,
    email_prefix: Optional[str],
    bounce_email: Optional[str],
    schema_content_file: Optional[IO[bytes]],
    workspace_id: Optional[int],
) -> None:
    schema_content = json.load(schema_content_file) if schema_content_file is not None else []
    with ELISClient() as elis:
        workspace_url = elis.get_workspace(workspace_id)["url"]

        schema_dict = elis.create_schema(f"{name} schema", schema_content)
        queue_dict = elis.create_queue(name, workspace_url, schema_dict["url"])

        inbox_dict = {"email": "no email-prefix specified"}
        if email_prefix is not None:
            inbox_dict = elis.create_inbox(
                f"{name} inbox", email_prefix, bounce_email, queue_dict["url"]
            )
    click.echo(f"{queue_dict['id']}, {inbox_dict['email']}")
