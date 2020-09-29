from typing import Tuple, Optional, Dict, Any, List

import click
from elisctl import option, argument
from elisctl.lib import QUEUES
from elisctl.lib.api_client import ElisClient
from tabulate import tabulate


@click.group("hook")
def cli() -> None:
    pass


@cli.command(name="create", help="Create a hook object.")
@argument.name
@option.queue(
    help="Queue IDs, that the hook will be associated with. "
    "Required field - will be assigned to an only queue automatically if not specified."
)
@option.active
@option.events
@option.config_url
@option.config_insecure_ssl
@option.config_secret
@click.pass_context
def create_command(
    ctx: click.Context,
    name: str,
    queue_ids: Tuple[int, ...],
    active: bool,
    events: Tuple[str, ...],
    config_url: str,
    config_secret: str,
    config_insecure_ssl: bool,
) -> None:

    with ElisClient(context=ctx.obj) as elis:
        if not queue_ids:
            queue_urls = [elis.get_queue()["url"]]
        else:
            queue_urls = []
            for id_ in queue_ids:
                queue_dict = elis.get_queue(id_)
                if queue_dict:
                    queue_urls.append(queue_dict["url"])

        response = elis.create_hook(
            name=name,
            queues=queue_urls,
            active=active,
            events=list(events),
            config_url=config_url,
            config_secret=config_secret,
            config_insecure_ssl=config_insecure_ssl,
        )
        click.echo(
            f"{response['id']}, {response['name']}, {response['queues']}, {response['events']}, {response['config']['url']}"
        )


@cli.command(name="list", help="List all hooks.")
@click.pass_context
def list_command(ctx: click.Context,):
    with ElisClient(context=ctx.obj) as elis:
        hooks_list = elis.get_hooks((QUEUES,))

    headers = ["id", "name", "events", "queues", "active", "url", "insecure_ssl"]

    def get_row(hook: dict) -> List[str]:
        res = [
            hook["id"],
            hook["name"],
            ", ".join(e for e in hook["events"]),
            ", ".join(str(q.get("id", "")) for q in hook["queues"]),
            hook["active"],
            hook["config"]["url"],
            hook["config"]["insecure_ssl"],
        ]
        try:
            secret_key = hook["config"]["secret"]
        except KeyError:
            pass
        else:
            res.append(secret_key)
            if "secret" not in headers:
                headers.append("secret")

        return res

    table = [get_row(hook) for hook in hooks_list]

    click.echo(tabulate(table, headers=headers))


@cli.command(name="change", help="Update a hook object.")
@argument.id_
@option.queue(related_object="hook")
@option.name
@option.events
@option.active
@option.config_url
@option.config_secret
@option.config_insecure_ssl
@click.pass_context
def change_command(
    ctx: click.Context,
    id_: int,
    queue_ids: Tuple[int, ...],
    name: Optional[str],
    events: Tuple[str, ...],
    active: Optional[bool],
    config_url: str,
    config_secret: str,
    config_insecure_ssl: bool,
) -> None:
    if not any([queue_ids, name, active, events, config_url, config_secret, config_insecure_ssl]):
        return

    data: Dict[str, Any] = {"config": {}}

    with ElisClient(context=ctx.obj) as elis:
        if queue_ids:
            data["queues"] = [elis.get_queue(queue)["url"] for queue in queue_ids]
        if name is not None:
            data["name"] = name
        if active is not None:
            data["active"] = active
        if events:
            data["events"] = list(events)
        if config_url is not None:
            data["config"].update({"url": config_url})
        if config_secret is not None:
            data["config"].update({"secret": config_secret})
        if config_insecure_ssl is not None:
            data["config"].update({"insecure_ssl": config_insecure_ssl})

        elis.patch(f"hooks/{id_}", data)


@cli.command(name="delete", help="Delete a hook.")
@argument.id_
@click.confirmation_option(
    prompt="This will delete the hook deployed on the queue. Do you want to continue?"
)
@click.pass_context
def delete_command(ctx: click.Context, id_: str) -> None:
    with ElisClient(context=ctx.obj) as elis:
        url = elis.url
        elis.delete(to_delete={f"{id_}": f"{url}/hooks/{id_}"}, item="hook")
