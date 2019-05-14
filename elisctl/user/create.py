from itertools import chain
from typing import Optional, Tuple

import click

from elisctl.lib import QUEUES, generate_secret
from elisctl.lib.api_client import ELISClient
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

        workspaces = api.get_workspaces(organization=organization_dict["id"], sideloads=(QUEUES,))
        queues = chain.from_iterable(w[str(QUEUES)] for w in workspaces)
        queue_urls = [q["url"] for q in queues if q["id"] in queue_id]

        response = api.create_user(
            username, organization_dict["url"], queue_urls, password, group, locale
        )
        click.echo(f"{response['id']}, {password}")
