from itertools import chain

from tabulate import tabulate
from typing import Tuple, Optional, List, Dict

import click
from elisctl import option
from elisctl.lib import USERS
from elisctl.lib.api_client import ELISClient


@click.group("user_assignment")
def cli() -> None:
    """Assignment of users to queues"""
    pass  # pragma: no cover


@cli.command(name="list")
@option.user(required=False, help="User IDs, which the queues will be filtered by.")
@option.queue(required=False, help="Queue IDs, which the users will be filtered by.")
@click.pass_context
def list_command(ctx: click.Context, user_ids: Tuple[int], queue_ids: Tuple[int]) -> None:
    """List all users and their assignments to queues."""
    with ELISClient(context=ctx.obj) as elis:
        queue_users = elis.get_queues((USERS,), users=user_ids)

    user_queues: Dict[int, List[List[Optional[str]]]] = {}
    for queue in queue_users:
        if queue_ids and int(queue["id"]) not in queue_ids:
            continue
        for user in queue["users"]:
            user_id = int(user["id"])
            if user_ids and user_id not in user_ids:
                continue

            if user_id not in user_queues:
                user_queues[user_id] = [[user["id"], user["username"], queue["id"], queue["name"]]]
            else:
                user_queues[user_id].append([None, None, queue["id"], queue["name"]])
    user_queues = dict(sorted(user_queues.items()))
    click.echo(
        tabulate(
            chain.from_iterable(user_queues.values()),
            headers=["id", "username", "queue id", "queue name"],
        )
    )
