from typing import List

import click

from elisctl.lib.api_client import APIClient, get_json


@click.command(name="create", short_help="Create user.")
@click.argument("username")
@click.argument("password")
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
    username: str, password: str, queues: List[str], group: str, locale: str
) -> None:
    """
    Create user with USERNAME and PASSWORD and add him to QUEUES specified by ids.
    """
    with APIClient() as api:

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

        api.post(
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
