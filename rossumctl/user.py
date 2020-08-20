from itertools import chain
from typing import Any, Dict, Optional, Tuple

import click
from tabulate import tabulate

from rossumctl import argument, option
from rossumctl.lib import GROUPS, QUEUES, USERS, generate_secret
from rossumctl.lib.api_client import RossumClient


@click.group("user")
def cli() -> None:
    pass


@cli.command(name="create", short_help="Create user.")
@click.argument("username")
@option.password
@option.queue(related_object="user", required=True)
@option.organization
@option.group
@option.locale
@click.pass_context
def create_command(
    ctx: click.Context,
    username: str,
    password: Optional[str],
    queue_ids: Tuple[int],
    organization_id: Optional[int],
    group: str,
    locale: str,
) -> None:
    """
    Create user with USERNAME and add him to QUEUES specified by ids.
    """
    password = password or generate_secret()
    with RossumClient(context=ctx.obj) as rossum:
        if rossum.get_users(username=username):
            raise click.ClickException(f"User with username {username} already exists.")
        organization = rossum.get_organization(organization_id)

        workspaces = rossum.get_workspaces(organization=organization["id"], sideloads=(QUEUES,))
        queues = chain.from_iterable(w[str(QUEUES)] for w in workspaces)
        queue_urls = [q["url"] for q in queues if q["id"] in queue_ids]

        response = rossum.create_user(
            username, organization["url"], queue_urls, password, group, locale
        )
        click.echo(f"{response['id']}, {password}")


@cli.command(name="list", help="List all users.")
@click.pass_context
def list_command(ctx: click.Context,):
    with RossumClient(context=ctx.obj) as rossum:
        users_list = rossum.get_users((QUEUES, GROUPS), is_active=True)

    table = [
        [
            user["id"],
            user["username"],
            ", ".join(str(g["name"]) for g in user[str(GROUPS)]),
            ", ".join(str(q["id"]) for q in user[str(QUEUES)]),
        ]
        for user in users_list
    ]

    click.echo(tabulate(table, headers=["id", "username", "groups", "queues"]))


@cli.command(name="change", help="Change a user.")
@argument.id_
@option.queue(related_object="user")
@option.group(default=None, show_default=False)
@option.locale(default=None, show_default=False)
@option.password(help=None)
@click.pass_context
def change_command(
    ctx: click.Context,
    id_: int,
    queue_ids: Tuple[int],
    group: Optional[str],
    locale: Optional[str],
    password: Optional[str],
) -> None:
    if not any([queue_ids, group, locale, password]):
        return

    data: Dict[str, Any] = {}
    if password is not None:
        data["password"] = password

    with RossumClient(context=ctx.obj) as rossum:
        if queue_ids:
            data[str(QUEUES)] = [rossum.get_queue(queue)["url"] for queue in queue_ids]
        if group is not None:
            data[str(GROUPS)] = [g["url"] for g in rossum.get_groups(group_name=group)]
        if locale is not None:
            ui_settings = rossum.get_user(id_)["ui_settings"]
            data["ui_settings"] = {**ui_settings, "locale": locale}

        rossum.patch(f"{USERS}/{id_}", data)


@cli.command(name="delete", help="Delete a user.")
@argument.id_
@click.confirmation_option()
@click.pass_context
def delete_command(ctx: click.Context, id_: int) -> None:
    with RossumClient(context=ctx.obj) as rossum:
        rossum.patch(f"{USERS}/{id_}", {"is_active": False})
