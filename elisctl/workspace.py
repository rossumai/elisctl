from typing import Optional, Dict, Any

import click
from tabulate import tabulate

from elisctl import argument, option
from elisctl.lib import QUEUES
from elisctl.lib.api_client import ELISClient, get_json


@click.group("workspace")
def cli() -> None:
    pass


@cli.command(name="create", short_help="Create workspace.")
@click.argument("name")
@option.organization
@click.pass_context
def create_command(ctx: click.Context, name: str, organization_id: Optional[int]) -> None:
    with ELISClient(context=ctx.obj) as elis:
        organization_url = elis.get_organization(organization_id)["url"]

        res = elis.post("workspaces", {"name": name, "organization": organization_url})
    workspace_dict = get_json(res)
    click.echo(workspace_dict["id"])


@cli.command(name="list", help="List all workspaces.")
@click.pass_context
def list_command(ctx: click.Context,):
    with ELISClient(context=ctx.obj) as elis:
        workspaces = elis.get_workspaces((QUEUES,))

    table = [
        [
            workspace["id"],
            workspace["name"],
            ", ".join(str(q.get("id", "")) for q in workspace["queues"]),
        ]
        for workspace in workspaces
    ]

    click.echo(tabulate(table, headers=["id", "name", "queues"]))


@cli.command(name="delete", help="Delete a workspace.")
@argument.id_
@click.confirmation_option()
@click.pass_context
def delete_command(ctx: click.Context, id_: int) -> None:
    with ELISClient(context=ctx.obj) as elis:
        workspace = elis.get_workspace(id_)
        queues = elis.get_queues(workspace=workspace["id"])
        documents = {}
        for queue in queues:
            res, _ = elis.get_paginated(
                "annotations",
                {"page_size": 50, "queue": queue["id"], "sideload": "documents"},
                key="documents",
            )
            documents.update({d["id"]: d["url"] for d in res})

        elis.delete({workspace["id"]: workspace["url"], **documents})


@cli.command(name="change", help="Change a workspace.")
@argument.id_
@option.name
@click.pass_context
def change_command(ctx: click.Context, id_: str, name: Optional[str]) -> None:
    if not any([name]):
        return

    data: Dict[str, Any] = {}
    if name is not None:
        data["name"] = name

    with ELISClient(context=ctx.obj) as elis:
        elis.patch(f"workspaces/{id_}", data)
