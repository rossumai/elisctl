from typing import Optional, Tuple

import click

from elisctl.lib import generate_secret
from elisctl.lib.api_client import ELISClient, get_json
from elisctl.user.options import group_option, locale_option, queue_option, password_option


@click.command(name="create", short_help="Create user.")
@click.argument("username")
@password_option
@queue_option
@click.option("-o", "--organization-id", type=int, help="Organization ID.", hidden=True)
@group_option
@locale_option
@click.pass_context
def create_command(
    ctx: click.Context,
    username: str,
    password: Optional[str],
    queue_id: Tuple[int],
    organization_id: Optional[int],
    group: str,
    locale: str,
) -> None:
    """
    Create user with USERNAME and add him to QUEUES specified by ids.
    """
    password = password or generate_secret()
    with ELISClient(context=ctx.obj) as api:
        if api.get_users(username=username):
            raise click.ClickException(f"User with username {username} already exists.")
        organization_dict = api.get_organization(organization_id)

        workspace_urls = {
            w["url"]
            for w in get_json(api.get("workspaces", {"organization": organization_dict["id"]}))[
                "results"
            ]
        }
        queue_urls = []
        for queue in queue_id:
            queue_dict = get_json(api.get(f"queues/{queue}"))
            if queue_dict["workspace"] in workspace_urls:
                queue_urls.append(queue_dict["url"])

        response = api.post(
            "users",
            {
                "username": username,
                "email": username,
                "organization": organization_dict["url"],
                "password": password,
                "groups": [g["url"] for g in api.get_groups(group_name=group)],
                "queues": queue_urls,
                "ui_settings": {"locale": locale},
            },
        )
        click.echo(f"{get_json(response)['id']}, {password}")
