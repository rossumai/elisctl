import secrets
import string
from typing import Optional, Tuple

import click

from elisctl.lib.api_client import APIClient, get_json


@click.command(name="create", short_help="Create user.")
@click.argument("username")
@click.option("-p", "--password", type=str, required=False, help="Generated, if not specified.")
@click.option(
    "-q",
    "--queue-id",
    type=int,
    multiple=True,
    help="Queue IDs, which the user will be associated with.",
)
@click.option("-o", "--organization-id", type=int, help="Organization ID.", hidden=True)
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
    password = password or _generate_password()
    with APIClient() as api:
        _check_user_does_not_exists(api, username)
        organization_dict = _get_organization(api, organization_id)

        workspace_urls = {
            w["url"]
            for w in get_json(api.get("workspaces", {"organization": organization_dict["id"]}))[
                "results"
            ]
        }
        queue_urls = []
        for queue in queue_id:
            queue_dict = get_json(api.get(f"queues/{queue}"))
            if queue_dict["workspace"] in workspace_urls:
                queue_urls.append(queue_dict["url"])

        groups = [g["url"] for g in get_json(api.get("groups", {"name": group}))["results"]]

        response = api.post(
            "users",
            {
                "username": username,
                "email": username,
                "organization": organization_dict["url"],
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


def _get_organization(api: APIClient, organization_id: Optional[int] = None) -> dict:
    if organization_id is None:
        user_url = get_json(api.get("auth/user"))["url"]
        organziation_url = get_json(api.get_url(user_url))["organization"]
        res = api.get_url(organziation_url)
    else:
        res = api.get(f"organizations/{organization_id}")
    return get_json(res)
