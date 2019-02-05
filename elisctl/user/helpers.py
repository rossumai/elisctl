from typing import Optional, List

from elisctl.lib.api_client import APIClient, get_json


def get_groups(api: APIClient, group_name: Optional[str]) -> List[str]:
    if group_name is None:
        return []
    return [g["url"] for g in get_json(api.get("groups", {"name": group_name}))["results"]]
