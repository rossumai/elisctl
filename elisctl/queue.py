from typing import Optional, Dict, Any, List, Tuple

import click
from tabulate import tabulate
from elisctl import argument, option
from elisctl.lib import INBOXES, WORKSPACES, SCHEMAS, USERS, HOOKS
from elisctl.lib.api_client import ElisClient, get_json

locale_option = click.option(
    "--locale",
    type=str,
    help="Document locale - passed to the Data Extractor, may influence e.g. date parsing.",
)


@click.group("queue")
def cli() -> None:
    pass


@cli.command(name="create", help="Create queue.")
@click.argument("name")
@option.schema_content(required=True)
@option.email_prefix
@option.bounce_email
@option.workspace_id
@option.connector_id
@locale_option
@option.hook_id
@click.pass_context
def create_command(
    ctx: click.Context,
    name: str,
    schema_content: List[dict],
    email_prefix: Optional[str],
    bounce_email: Optional[str],
    workspace_id: Optional[int],
    connector_id: Optional[int],
    hook_id: Optional[Tuple[int, ...]],
    locale: Optional[str],
) -> None:
    if email_prefix is not None and bounce_email is None:
        raise click.ClickException("Inbox cannot be created without specified bounce email.")

    with ElisClient(context=ctx.obj) as elis:
        workspace_url = elis.get_workspace(workspace_id)["url"]
        connector_url = (
            get_json(elis.get(f"connectors/{connector_id}"))["url"]
            if connector_id is not None
            else None
        )

        hooks_urls = []
        if hook_id:
            for hook in hook_id:
                hook_url = get_json(elis.get(f"hooks/{hook}"))["url"]
                hooks_urls.append(hook_url)

        schema_dict = elis.create_schema(f"{name} schema", schema_content)
        queue_dict = elis.create_queue(
            name, workspace_url, schema_dict["url"], connector_url, hooks_urls, locale
        )

        inbox_dict = {"email": "no email-prefix specified"}
        if email_prefix is not None:
            inbox_dict = elis.create_inbox(
                f"{name} inbox", email_prefix, bounce_email, queue_dict["url"]
            )
    click.echo(f"{queue_dict['id']}, {inbox_dict['email']}")


@cli.command(name="list", help="List all queues.")
@click.pass_context
def list_command(ctx: click.Context,) -> None:
    with ElisClient(context=ctx.obj) as elis:
        queues = elis.get_queues((WORKSPACES, INBOXES, SCHEMAS, USERS, HOOKS))

    table = [
        [
            queue["id"],
            queue["name"],
            str(queue["workspace"].get("id", "")),
            queue["inbox"].get("email", ""),
            str(queue["schema"].get("id", "")),
            ", ".join(str(q.get("id", "")) for q in queue["users"]),
            queue["connector"],
            ", ".join(str(q.get("id", "")) for q in queue["hooks"]),
        ]
        for queue in queues
    ]

    click.echo(
        tabulate(
            table,
            headers=["id", "name", "workspace", "inbox", "schema", "users", "connector", "hooks"],
        )
    )


@cli.command(name="delete", help="Delete a queue.")
@argument.id_
@click.confirmation_option(
    prompt="This will delete ALL DOCUMENTS in the queue. Do you want to continue?"
)
@click.pass_context
def delete_command(ctx: click.Context, id_: int) -> None:
    with ElisClient(context=ctx.obj) as elis:
        queue = elis.get_queue(id_)
        elis.delete({queue["id"]: queue["url"]})


@cli.command(name="change", help="Change a queue.")
@argument.id_
@option.name
@option.schema_content
@option.connector_id
@option.email_prefix
@option.bounce_email
@option.hook_id
@locale_option
@click.pass_context
def change_command(
    ctx: click.Context,
    id_: int,
    name: Optional[str],
    schema_content: Optional[List[dict]],
    email_prefix: Optional[str],
    bounce_email: Optional[str],
    connector_id: Optional[int],
    hook_id: Optional[Tuple[int, ...]],
    locale: Optional[str],
) -> None:

    if not any([name, schema_content, email_prefix, bounce_email, connector_id, locale, hook_id]):
        return

    data: Dict[str, Any] = {}

    if name is not None:
        data["name"] = name

    if locale is not None:
        data["locale"] = locale

    with ElisClient(context=ctx.obj) as elis:
        if email_prefix or bounce_email:
            queue_dict = elis.get_queue(id_)
            if not queue_dict["inbox"]:
                inbox_dict = _create_inbox(elis, queue_dict, email_prefix, bounce_email, name)
            else:
                inbox_dict = _patch_inbox(elis, queue_dict, email_prefix, bounce_email)
            click.echo(
                f"{inbox_dict['id']}, {inbox_dict['email']}, {inbox_dict['bounce_email_to']}"
            )

        if connector_id is not None:
            data["connector"] = get_json(elis.get(f"connectors/{connector_id}"))["url"]

        if hook_id:
            hooks_urls = []
            for hook in hook_id:
                hook_url = get_json(elis.get(f"hooks/{hook}"))["url"]
                hooks_urls.append(hook_url)
                data["hooks"] = hooks_urls

        if schema_content is not None:
            name = name or elis.get_queue(id_)["name"]
            schema_dict = elis.create_schema(f"{name} schema", schema_content)
            data["schema"] = schema_dict["url"]

        if data:
            elis.patch(f"queues/{id_}", data)


def _create_inbox(
    elis: ElisClient,
    queue_dict: dict,
    email_prefix: Optional[str],
    bounce_email: Optional[str],
    name: Optional[str],
) -> dict:
    return elis.create_inbox(
        f"{name or queue_dict['name']} inbox", email_prefix, bounce_email, queue_dict["url"]
    )


def _patch_inbox(
    elis: ElisClient, queue_dict: dict, email_prefix: Optional[str], bounce_email: Optional[str]
) -> dict:
    inbox_data: Dict[str, Any] = {}

    if email_prefix:
        inbox_data["email_prefix"] = email_prefix

    if bounce_email:
        inbox_data["bounce_email_to"] = bounce_email
        inbox_data["bounce_unprocessable_attachments"] = True

    _, inbox_id = queue_dict["inbox"].rsplit("/", 1)
    return get_json(elis.patch(f"inboxes/{inbox_id}", inbox_data))
