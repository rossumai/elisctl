from typing import Tuple, Optional, Dict, Any

import click
from tabulate import tabulate

from elisctl.lib.api_client import APIClient, get_json
from elisctl.user import create
from elisctl.user.helpers import get_groups
from elisctl.user.options import queue_option, group_option, locale_option, password_option


@click.group("user")
def cli() -> None:
    pass


cli.add_command(create.create_command)


@cli.command(name="list", help="List all users.")
def list_command():
    with APIClient() as api_client:
        users_list, _ = api_client.get_paginated("users", {"is_active": True})
        groups_list, _ = api_client.get_paginated("groups")
        queues_list, _ = api_client.get_paginated("queues")
    groups = {group["url"]: group.get("name", "") for group in groups_list}
    queues = {queue["url"]: queue.get("id", "") for queue in queues_list}

    table = [
        [
            user["id"],
            user["username"],
            ", ".join(str(groups[g]) for g in user["groups"]),
            ", ".join(str(queues[q]) for q in user["queues"]),
        ]
        for user in users_list
    ]

    click.echo(tabulate(table, headers=["id", "username", "groups", "queues"]))


@cli.command(name="change", help="Change a user.")
@click.argument("id_", metavar="ID", type=str)
@queue_option
@group_option(default=None, show_default=False)
@locale_option(default=None, show_default=False)
@password_option(help=None)
def change_command(
    id_: str,
    queue_id: Tuple[str],
    group: Optional[str],
    locale: Optional[str],
    password: Optional[str],
) -> None:
    if not any([queue_id, group, locale, password]):
        return

    data: Dict[str, Any] = {}
    if password is not None:
        data["password"] = password

    with APIClient() as api_client:
        if queue_id:
            data["queues"] = [
                get_json(api_client.get(f"queues/{queue}"))["url"] for queue in queue_id
            ]
        if group is not None:
            data["groups"] = get_groups(api_client, group)
        if locale is not None:
            ui_settings = get_json(api_client.get(f"users/{id_}"))["ui_settings"]
            data["ui_settings"] = {**ui_settings, "locale": locale}

        api_client.patch(f"users/{id_}", data)


@cli.command(name="delete", help="Delete a user.")
@click.argument("id_", metavar="ID", type=str)
@click.confirmation_option()
def delete_command(id_: str) -> None:
    with APIClient() as api_client:
        api_client.patch(f"users/{id_}", {"is_active": False})
