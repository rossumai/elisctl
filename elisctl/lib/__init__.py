import json
import secrets
import string
from contextlib import suppress
from dataclasses import dataclass

from typing import Iterable, Iterator, Tuple, Union, Dict, List

# todo: use TypedDict if available https://www.python.org/dev/peps/pep-0589/
# todo: use Recursion (see the following) when https://github.com/python/mypy/issues/731 is ready
# DataPointDictItem = Union[str, int, "DataPointDict", None, "DataPoints"]
DataPointDictItem = Union[str, int, dict, None, list]
DataPointDict = Dict[str, DataPointDictItem]
DataPoints = List[DataPointDict]


def split_dict_params(
    datapoint_parameters: Iterable[str]
) -> Iterator[Tuple[str, DataPointDictItem]]:
    for param in datapoint_parameters:
        key, value = param.split("=", 1)
        with suppress(ValueError):
            value = json.loads(value)
        yield key, value


def generate_secret(length: int = 10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@dataclass(frozen=True)
class APIObject:
    NOT_SET = "NOT_SET"

    plural: str
    singular: str = NOT_SET

    def __post_init__(self) -> None:
        if self.singular is self.NOT_SET:
            # https://docs.python.org/3/library/dataclasses.html#frozen-instances
            object.__setattr__(self, "singular", self.plural.rstrip("s"))

    def __str__(self) -> str:
        return self.plural

    # todo: add list and detail methods (the base_url needs to be somehow obtained)


ORGANIZATIONS = APIObject("organizations")
WORKSPACES = APIObject("workspaces")
QUEUES = APIObject("queues")
INBOXES = APIObject("inboxes", "inbox")
CONNECTORS = APIObject("connectors")
HOOKS = APIObject("hooks")
SCHEMAS = APIObject("schemas")
USERS = APIObject("users")
GROUPS = APIObject("groups")
ANNOTATIONS = APIObject("annotations")
PAGES = APIObject("pages")
