import secrets
import string
from typing import List, Optional

import click

from elisctl.lib.api_client import APIClient, get_json


@click.command(name="create", short_help="Create user.")
@click.argument("username")
@click.option("-p", "--password", type=str, required=False, help="Generated, if not specified.")
@click.argument("queues", nargs=-1, type=int)
@click.option(
    "-g",
    "--group",
    default="annotator",
    type=click.Choice(["annotator", "admin", "viewer"]),
    help="Permission group.",
    show_default=True,
)
@click.option(
    "-l",
    "--locale",
    default="en",
    type=click.Choice(["en", "cs"]),
    help="UI locale",
    show_default=True,
)
def create_command(
    username: str, password: Optional[str], queues: List[str], group: str, locale: str
) -> None:
    """
    Create user with USERNAME and add him to QUEUES specified by ids.
    """
    password = password or _generate_password()
    with APIClient() as api:
        _check_user_does_not_exists(api, username)

        queue_urls = []
        organizations = set()
        for queue in queues:
            queue_dict = get_json(api.get(f"queues/{queue}"))
            queue_urls.append(queue_dict["url"])
            workspace_dict = get_json(api.get_url(queue_dict["workspace"]))
            organizations.add(workspace_dict["organization"])

        if len(organizations) > 1:
            raise click.ClickException(f"User can be in only 1 organization.")
        elif not organizations:
            raise click.ClickException(f"User must be in at least 1 organization.")
        else:
            organization_url = organizations.pop()

        groups = [g["url"] for g in get_json(api.get("groups", {"name": group}))["results"]]

        response = api.post(
            "users",
            {
                "username": username,
                "email": username,
                "organization": organization_url,
                "password": password,
                "groups": groups,
                "queues": queue_urls,
                "ui_settings": {"locale": locale},
            },
        )
        click.echo(f"{get_json(response)['id']}, {password}")


def _check_user_does_not_exists(api: APIClient, username: str) -> None:
    total_users = get_json(api.get(f"users", {"username": username}))["pagination"]["total"]
    if total_users:
        raise click.ClickException(f"User with username {username} already exists.")


def _generate_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(10))
