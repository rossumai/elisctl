import json
from contextlib import suppress
from typing import Iterable, Iterator, Tuple, Union


def split_dict_params(
    datapoint_parameters: Iterable[str]
) -> Iterator[Tuple[str, Union[str, int, dict, None, list]]]:
    for param in datapoint_parameters:
        key, value = param.split("=", 1)
        with suppress(ValueError):
            value = json.loads(value)
        yield key, value
