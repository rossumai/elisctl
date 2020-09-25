from typing import Optional, Dict, Any

import click
from tabulate import tabulate

from rossumctl import argument, option
from rossumctl.lib import QUEUES
from rossumctl.lib.api_client import RossumClient, get_json


@click.group("workspace")
def cli() -> None:
    pass


@cli.command(name="create", short_help="Create workspace.")
@click.argument("name")
@option.organization
@click.pass_context
def create_command(ctx: click.Context, name: str, organization_id: Optional[int]) -> None:
    with RossumClient(context=ctx.obj) as rossum:
        organization_url = rossum.get_organization(organization_id)["url"]

        res = rossum.post("workspaces", {"name": name, "organization": organization_url})
    workspace_dict = get_json(res)
    click.echo(workspace_dict["id"])


@cli.command(name="list", help="List all workspaces.")
@click.pass_context
def list_command(ctx: click.Context,):
    with RossumClient(context=ctx.obj) as rossum:
        workspaces = rossum.get_workspaces((QUEUES,))

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
    with RossumClient(context=ctx.obj) as rossum:
        workspace = rossum.get_workspace(id_)
        queues = rossum.get_queues(workspace=workspace["id"])
        documents = {}
        for queue in queues:
            res, _ = rossum.get_paginated(
                "annotations",
                {"page_size": 50, "queue": queue["id"], "sideload": "documents"},
                key="documents",
            )
            documents.update({d["id"]: d["url"] for d in res})

        rossum.delete({workspace["id"]: workspace["url"], **documents})


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

    with RossumClient(context=ctx.obj) as rossum:
        rossum.patch(f"workspaces/{id_}", data)
