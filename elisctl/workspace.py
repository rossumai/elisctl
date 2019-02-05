from typing import Optional

import click

from elisctl.lib.api_client import ELISClient, get_json
from elisctl.options import organization_option


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
