#!/usr/bin/env python3
import difflib
import json
import pprint

import click
import re
from jsondiff import diff as json_diff, JsonDumper
from typing import Iterable, IO

from elisctl.lib import split_dict_params

DIFF_TYPES = ["jsondiff", "difflib"]
DIFF_RE = re.compile(r"^[+-^]")


@click.command("compare", help="Compare 2 json files.")
@click.argument("json1", type=click.File("rb"))
@click.argument("json2", type=click.File("rb"))
@click.option("--method", "-m", type=click.Choice(DIFF_TYPES), default=DIFF_TYPES[0])
@click.option("--option", "-o", "options", multiple=True, type=str)
def cli(json1: IO[str], json2: IO[str], method: str, options: Iterable[str]) -> None:
    try:
        options_dict = dict(split_dict_params(options))
    except ValueError as e:
        raise click.BadArgumentUsage("Expecting <key>=<value> pairs.") from e

    d1 = json.load(json1)
    d2 = json.load(json2)
    if method == "difflib":
        diff = _difflib(d1, d2, **options_dict)
    elif method == "jsondiff":
        diff = _json_diff(d1, d2, **options_dict)
    else:
        raise NotImplementedError

    click.echo(diff)


def _difflib(d1: dict, d2: dict, **kwargs) -> str:
    diff_list = difflib.ndiff(pprint.pformat(d1).splitlines(), pprint.pformat(d2).splitlines())
    if str(kwargs.get("fulldiff", False)).lower() in ("true", "t", "1"):
        return "\n" + "\n".join(diff_list)
    else:
        return "\n" + "\n".join(d for d in diff_list if DIFF_RE.match(d))


def _json_diff(d1: dict, d2: dict, **kwargs) -> str:
    dumper = JsonDumper(indent=2)
    kwargs = {"syntax": "symmetric", **kwargs}
    return json_diff(d1, d2, **kwargs, dumper=dumper, dump=True)
