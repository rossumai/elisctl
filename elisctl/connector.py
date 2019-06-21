import secrets
import string
from typing import Tuple, Optional, Dict, Any, List

import click
from elisctl import option, argument
from elisctl.lib import QUEUES
from elisctl.lib.api_client import ELISClient
from tabulate import tabulate


@click.group("connector")
def cli() -> None:
    pass


@cli.command(name="create", help="Create a connector object.")
@argument.name
@option.queue
@option.service_url
@option.auth_token
@option.params
@option.asynchronous
@click.pass_context
def create_command(
    ctx: click.Context,
    name: str,
    queue_ids: Tuple[int],
    service_url: str,
    auth_token: str,
    params: Optional[str],
    asynchronous: Optional[bool],
) -> None:
    token = auth_token or _generate_token()

    with ELISClient(context=ctx.obj) as elis:
        queue_urls = []
        for id_ in queue_ids:
            queue_dict = elis.get_queue(id_)
            if queue_dict:
                queue_urls.append(queue_dict["url"])

        response = elis.create_connector(
            name=name,
            queues=queue_urls,
            service_url=service_url,
            authorization_token=token,
            params=params,
            asynchronous=asynchronous,
        )
        click.echo(f"{response['id']}, {response['name']}")


@cli.command(name="list", help="List all connectors.")
@click.pass_context
def list_command(ctx: click.Context,):
    with ELISClient(context=ctx.obj) as elis:
        connectors_list = elis.get_connectors((QUEUES,))

    headers = ["id", "name", "service url", "queues", "params", "asynchronous"]

    def get_row(connector: dict) -> List[str]:
        res = [
            connector["id"],
            connector["name"],
            connector["service_url"],
            ", ".join(str(q.get("id", "")) for q in connector["queues"]),
            connector["params"],
            connector["asynchronous"],
        ]
        try:
            token = connector["authorization_token"]
        except KeyError:
            pass
        else:
            res.append(token)
            if "authorization_token" not in headers:
                headers.append("authorization_token")

        return res

    table = [get_row(connector) for connector in connectors_list]

    click.echo(tabulate(table, headers=headers))


@cli.command(name="change", help="Update a connector object.")
@argument.id_
@option.queue
@option.name
@option.service_url
@option.auth_token
@option.params
@option.asynchronous
@click.pass_context
def change_command(
    ctx: click.Context,
    id_: str,
    queue_ids: Tuple[int],
    name: Optional[str],
    service_url: str,
    auth_token: str,
    params: Optional[str],
    asynchronous: Optional[bool],
) -> None:
    if not any([queue_ids, service_url, auth_token, params, asynchronous]):
        return

    data: Dict[str, Any] = {}

    with ELISClient(context=ctx.obj) as elis:
        if queue_ids:
            data["queues"] = [elis.get_queue(queue)["url"] for queue in queue_ids]
        if name is not None:
            data["name"] = name
        if service_url is not None:
            data["service_url"] = service_url
        if auth_token is not None:
            data["authorization_token"] = auth_token
        if params is not None:
            data["params"] = params
        if asynchronous is not None:
            data["asynchronous"] = asynchronous

        elis.patch(f"connectors/{id_}", data)


@cli.command(name="delete", help="Delete a connector.")
@argument.id_
@click.confirmation_option(
    prompt="This will delete the connector deployed on the queue. Do you want to continue?"
)
@click.pass_context
def delete_command(ctx: click.Context, id_: str) -> None:
    with ELISClient(context=ctx.obj) as elis:
        url = elis.url
        elis.delete(to_delete={f"{id_}": f"{url}/connectors/{id_}"}, item="connector")


def _generate_token():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(36))
