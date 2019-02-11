import json
from typing import Optional, IO, Dict, Any

import click
from tabulate import tabulate

from elisctl.arguments import id_argument
from elisctl.lib.api_client import ELISClient, get_json
from elisctl.options import (
    bounce_email_option,
    connector_id_option,
    email_prefix_option,
    name_option,
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
@schema_content_file_option(required=True)
@email_prefix_option
@bounce_email_option
@workspace_id_option
@connector_id_option
@locale_option
def create_command(
    name: str,
    schema_content_file: IO[bytes],
    email_prefix: Optional[str],
    bounce_email: Optional[str],
    workspace_id: Optional[int],
    connector_id: Optional[int],
    locale: Optional[str],
) -> None:
    schema_content = json.load(schema_content_file)
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


@cli.command(name="list", help="List all queues.")
@workspace_id_option
def list_command(workspace_id: Optional[int]) -> None:
    with ELISClient() as elis:
        queues = elis.get_queues(("workspaces",))

    table = [[queue["id"], queue["name"], str(queue["workspace"]["id"])] for queue in queues]

    click.echo(tabulate(table, headers=["id", "name", "workspace"]))


@cli.command(name="delete", help="Delete a queue.")
@id_argument
@click.confirmation_option(
    prompt="This will delete ALL DOCUMENTS in the queue. Do you want to continue?"
)
def delete_command(id_: int) -> None:
    with ELISClient() as elis:
        queue = elis.get_queue(id_)
        elis.delete({queue["id"]: queue["url"]})


@cli.command(name="change", help="Change a queue.")
@id_argument
@name_option
@schema_content_file_option
@connector_id_option
@locale_option
def change_command(
    id_: str,
    name: Optional[str],
    schema_content_file: Optional[IO[bytes]],
    connector_id: Optional[int],
    locale: Optional[str],
) -> None:
    if not any([name]):
        return

    data: Dict[str, Any] = {}
    if name is not None:
        data["name"] = name
    if locale is not None:
        data["locale"] = locale
    schema_content = json.load(schema_content_file) if schema_content_file is not None else []

    with ELISClient() as elis:
        if connector_id is not None:
            data["connector"] = get_json(elis.get(f"connectors/{connector_id}"))["url"]
        if schema_content:
            schema_dict = elis.create_schema(f"{name} schema", schema_content)
            data["schema"] = schema_dict["url"]
        elis.patch(f"queues/{id_}", data)
