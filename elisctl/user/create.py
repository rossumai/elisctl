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
    with ELISClient(context=ctx.obj) as elis:
        if elis.get_users(username=username):
            raise click.ClickException(f"User with username {username} already exists.")
        organization = elis.get_organization(organization_id)

        workspaces = elis.get_workspaces(organization=organization["id"], sideloads=(QUEUES,))
        queues = chain.from_iterable(w[str(QUEUES)] for w in workspaces)
        queue_urls = [q["url"] for q in queues if q["id"] in queue_id]

        response = elis.create_user(
            username, organization["url"], queue_urls, password, group, locale
        )
        click.echo(f"{response['id']}, {password}")
