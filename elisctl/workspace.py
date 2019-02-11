from typing import Optional, Dict, Any

import click
from tabulate import tabulate

from elisctl.arguments import id_argument
from elisctl.lib.api_client import ELISClient, get_json
from elisctl.options import organization_option, name_option


@click.group("workspace")
def cli() -> None:
    pass


@cli.command(name="create", short_help="Create workspace.")
@click.argument("name")
@organization_option
def create_command(name: str, organization_id: Optional[int]) -> None:
    with ELISClient() as elis:
        organization_url = elis.get_organization(organization_id)["url"]

        res = elis.post("workspaces", {"name": name, "organization": organization_url})
    workspace_dict = get_json(res)
    click.echo(workspace_dict["id"])


@cli.command(name="list", help="List all workspaces.")
def list_command():
    with ELISClient() as elis:
        workspaces = elis.get_workspaces(("queues",))

    table = [
        [workspace["id"], workspace["name"], ", ".join(str(q["id"]) for q in workspace["queues"])]
        for workspace in workspaces
    ]

    click.echo(tabulate(table, headers=["id", "name", "queues"]))


@cli.command(name="delete", help="Delete a workspace.")
@id_argument
@click.confirmation_option(
    prompt="This will delete ALL QUEUES AND DOCUMENTS in the workspace. Do you want to continue?"
)
def delete_command(id_: int) -> None:
    with ELISClient() as elis:
        workspace = elis.get_workspace(id_)
        elis.delete({workspace["id"]: workspace["url"]})


@cli.command(name="change", help="Change a workspace.")
@id_argument
@name_option
def change_command(id_: str, name: Optional[str]) -> None:
    if not any([name]):
        return

    data: Dict[str, Any] = {}
    if name is not None:
        data["name"] = name

    with ELISClient() as elis:
        elis.patch(f"workspaces/{id_}", data)
