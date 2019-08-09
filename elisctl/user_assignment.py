from itertools import chain

from tabulate import tabulate
from typing import Tuple, Optional, List, Dict

import click
from elisctl import option
from elisctl.lib import USERS, QUEUES
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


@cli.command(name="add", help="Add user to queues.")
@option.user
@option.queue
@click.pass_context
def add_command(ctx: click.Context, user_ids: Tuple[int], queue_ids: Tuple[int]) -> None:
    with ELISClient(context=ctx.obj) as elis:
        for user_id in user_ids:
            user = elis.get_user(user_id)
            new_queues = user["queues"] + [elis.get_queue(q_id)["url"] for q_id in queue_ids]
            elis.patch(f"{USERS}/{user_id}", {str(QUEUES): new_queues})


@cli.command(name="remove", help="Remove user from queues.")
@option.user
@option.queue
@click.pass_context
def remove_command(ctx: click.Context, user_ids: Tuple[int], queue_ids: Tuple[int]) -> None:
    with ELISClient(context=ctx.obj) as elis:
        for user_id in user_ids:
            queues = elis.get_queues(users=[user_id])
            new_queues = [q["url"] for q in queues if int(q["id"]) not in queue_ids]
            elis.patch(f"{USERS}/{user_id}", {str(QUEUES): new_queues})
