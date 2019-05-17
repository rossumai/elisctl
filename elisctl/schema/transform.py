#!/usr/bin/env python3
import json
import warnings
from copy import deepcopy
from typing import List, Callable, Optional, IO, Tuple, Iterable, Dict, Union, Set

import click as click

from elisctl import argument, option
from elisctl.lib import split_dict_params

DataPointDictItem = Union[str, int, dict, None, list]
DataPointDict = Dict[str, DataPointDictItem]


@click.group("transform", help="Transform schema file content.")
@click.pass_context
@click.option(
    "--indent", default=2, type=int, show_default=True, help="Indentation of resulting JSON."
)
@click.option(
    "--ensure-ascii", is_flag=True, type=bool, help="Escape non-ASCII characters in resulting JSON."
)
@click.option("--sort-keys", is_flag=True, type=bool, help="Order keys in resulting JSON.")
@option.output_file
def cli(
    ctx: click.Context,
    indent: int,
    ensure_ascii: bool,
    sort_keys: bool,
    output_file: Optional[IO[str]],
) -> None:
    pass


@cli.command(name="substitute-options", help="Substitute options in existing enum datapoint.")
@click.pass_context
@argument.schema_file
@click.argument("id_", metavar="ID", type=str)
@click.argument("new_options", type=click.File("rb"))
def substitute_options_command(ctx: click.Context, new_options: IO[str], id_: str) -> List[dict]:
    options_dict = json.load(new_options)
    return traverse_datapoints(ctx.obj["SCHEMA"], substitute_options, id_=id_, options=options_dict)


@cli.command(name="remove", help="Remove datapoints.")
@click.pass_context
@argument.schema_file
@click.argument("ids", nargs=-1, type=str)
def remove_command(ctx: click.Context, ids: Tuple[str, ...]) -> List[dict]:
    return traverse_datapoints(ctx.obj["SCHEMA"], remove, ids=ids)


@cli.command(
    name="wrap-in-multivalue",
    short_help="Put all datapoints into a multivalue.",
    help="Put all datapoints into a multivalue (unless they are already in a multivalue).",
)
@click.pass_context
@argument.schema_file
@click.argument("exclude_ids", nargs=-1, type=str)
def wrap_in_multivalue_command(ctx: click.Context, exclude_ids: Tuple[str, ...]) -> List[dict]:
    return traverse_datapoints(ctx.obj["SCHEMA"], wrap_in_multivalue, exclude_ids=set(exclude_ids))


@cli.command(
    name="add",
    short_help="Create new datapoint.",
    help="""
Create new datapoint.

DATAPOINT_PARAMETERS are expected as <key>=<value> pairs, where <value> can be a json.
""",
)
@click.pass_context
@argument.schema_file
@click.argument("parent_id", type=str)
@click.argument("datapoint_parameters", nargs=-1, type=str)
@click.option(
    "--place-before",
    "-p",
    type=str,
    default=None,
    help="Id of datapoint which will follow the added datapoint.",
)
def add_command(
    ctx: click.Context,
    parent_id: str,
    datapoint_parameters: Iterable[str],
    place_before: Optional[str],
) -> List[dict]:
    try:
        datapoint_parameters_dict = dict(split_dict_params(datapoint_parameters))
    except ValueError as e:
        raise click.BadArgumentUsage("Expecting <key>=<value> pairs.") from e

    return traverse_datapoints(
        ctx.obj["SCHEMA"],
        add,
        parent_id=parent_id,
        datapoint_to_add=_new_datapoint(datapoint_parameters_dict),
        place_before=place_before,
    )


@cli.command(
    name="change",
    short_help="Change existing datapoint.",
    help="""
Change existing datapoint.

ID can be set to ALL, then all datapoints are changed.
DATAPOINT_PARAMETERS are expected as <key>=<value> pairs, where <value> can be a JSON.
""",
)
@click.pass_context
@argument.schema_file
@click.argument("id_", metavar="ID", type=str)
@click.argument("datapoint_parameters", nargs=-1, type=str)
@click.option(
    "-c",
    "--category",
    "categories",
    type=click.Choice(["datapoint", "multivalue", "tuple", "section"]),
    multiple=True,
    help="Change only datapoints of specified categories. Useful with <id> set to ALL. "
    "Multiple categories can be set.",
)
def change_command(
    ctx: click.Context, id_: str, datapoint_parameters: Iterable[str], categories: Tuple[str]
) -> List[dict]:
    try:
        datapoint_parameters_dict = dict(split_dict_params(datapoint_parameters))
    except ValueError as e:
        raise click.BadArgumentUsage("Expecting <key>=<value> pairs.") from e

    return traverse_datapoints(
        ctx.obj["SCHEMA"],
        change,
        id_=id_,
        to_change=datapoint_parameters_dict,
        filtered_categories=categories,
    )


@cli.command(name="move", help="Move datapoint to new parent datapoint.")
@click.pass_context
@argument.schema_file
@click.argument("source_id", type=str)
@click.argument("target_id", type=str)
def move_command(ctx: click.Context, source_id: str, target_id: str) -> List[dict]:
    source_dp = get(ctx.obj["SCHEMA"], id_=source_id)
    new_schema = traverse_datapoints(ctx.obj["SCHEMA"], remove, ids=(source_id,))
    return traverse_datapoints(new_schema, add, parent_id=target_id, datapoint_to_add=source_dp)


@cli.resultcallback()
@click.pass_context
def process_result(
    ctx: click.Context,
    result: List[dict],
    indent: int,
    ensure_ascii: bool,
    sort_keys: bool,
    output_file: Optional[IO[str]],
) -> None:
    output = json.dumps(result, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys)
    click.echo(output.encode("utf-8"), file=output_file, nl=False)


def traverse_datapoints(
    datapoints: List[dict], transformation: Callable, parent_categories: List[str] = None, **kwargs
) -> List[dict]:
    dummy_root = {"category": "root", "id": None, "children": datapoints}
    return _traverse_datapoints([dummy_root], transformation, parent_categories, **kwargs)[0][
        "children"
    ]


def _traverse_datapoints(
    datapoints: List[dict], transformation: Callable, parent_categories: List[str] = None, **kwargs
) -> List[dict]:
    new_datapoints = []
    parent_categories = parent_categories or []
    for datapoint in datapoints:
        new_datapoint = deepcopy(datapoint)
        category = datapoint["category"]
        if category != "datapoint":
            parent_categories_ = parent_categories[:] + [category]
            children = new_datapoint.pop("children", [])
            if category == "multivalue" and children:
                [new_datapoint["children"]] = _traverse_datapoints(
                    [children], transformation, parent_categories_, **kwargs
                )
            elif category == "multivalue":
                new_datapoint["children"] = None
            elif category in ("tuple", "section", "root"):
                new_datapoint["children"] = _traverse_datapoints(
                    children, transformation, parent_categories_, **kwargs
                )
        new_datapoint = transformation(new_datapoint, parent_categories, **kwargs)
        if new_datapoint:
            new_datapoints.append(new_datapoint)

    return new_datapoints


def substitute_options(
    datapoint: dict, parent_categories: List[str], id_: str, options: List[dict]
) -> dict:
    if (
        datapoint["category"] != "datapoint"
        or datapoint["type"] != "enum"
        or datapoint["id"] != id_
    ):
        return datapoint

    new_datapoint = deepcopy(datapoint)
    return {**new_datapoint, "options": options}


def remove(datapoint: dict, parent_categories: List[str], ids: Tuple[str, ...]) -> Optional[dict]:
    if datapoint["id"] in ids:
        if parent_categories and "multivalue" == parent_categories[-1]:
            warnings.warn("Cannot delete child of a multivalue.")
            return datapoint
        else:
            return None
    else:
        return datapoint


def wrap_in_multivalue(
    datapoint: dict, parent_categories: List[str], exclude_ids: Set[str]
) -> dict:
    if (
        "multivalue" in parent_categories
        or datapoint["category"] in ("multivalue", "section", "root")
        or datapoint["id"] in exclude_ids
    ):
        return datapoint
    return {
        "id": f'{datapoint["id"]}_multi',
        "label": datapoint["label"],
        "children": {"use_rir_content": True, **datapoint},
        "category": "multivalue",
        "max_occurrences": None,
        "min_occurrences": None,
    }


def add(
    datapoint: dict,
    parent_categories: List[str],
    parent_id: str,
    datapoint_to_add: dict,
    place_before: Optional[str] = None,
) -> dict:
    if datapoint["id"] != parent_id:
        return datapoint

    if datapoint["category"] in ("tuple", "section", "root"):
        new_datapoint = deepcopy(datapoint)
        if place_before is None:
            new_datapoint["children"].append(datapoint_to_add)
        else:
            new_datapoint["children"].insert(
                _find_index_of_id(place_before, new_datapoint["children"]), datapoint_to_add
            )
        return new_datapoint
    elif datapoint["category"] == "multivalue" and not datapoint.get("children"):
        new_datapoint = deepcopy(datapoint)
        new_datapoint["children"] = datapoint_to_add
        return new_datapoint
    elif datapoint["category"] == "multivalue":
        warnings.warn("Cannot add child to a filled multivalue.")
        return datapoint
    else:
        return datapoint


def _find_index_of_id(id_: str, children: List[dict]) -> int:
    for i, child in enumerate(children):
        if child["id"] == id_:
            return i
    else:
        raise click.ClickException(f"Not found ID '{id_}' to place behind.")


def change(
    datapoint: dict,
    parent_categories: List[str],
    id_: str,
    to_change: dict,
    filtered_categories: Tuple[str],
) -> dict:
    is_of_id = id_ in (datapoint["id"], "ALL")
    is_of_category = not filtered_categories or datapoint["category"] in filtered_categories
    if not (is_of_id and is_of_category):
        return datapoint
    else:
        return {**datapoint, **to_change}


def get(datapoints: List[dict], id_: str) -> Optional[dict]:
    res = None

    for datapoint in datapoints:
        if datapoint["id"] == id_:
            return datapoint

        category = datapoint["category"]
        if category in ("section", "tuple"):
            res = get(datapoint["children"], id_)
        elif category == "multivalue":
            res = get([datapoint["children"]], id_)
        if res is not None:
            return res
    return res


def _new_datapoint(datapoint_to_add: DataPointDict) -> DataPointDict:
    try:
        id_ = datapoint_to_add.pop("id")
    except KeyError as e:
        raise click.BadArgumentUsage("Missing key 'id'.") from e

    category = datapoint_to_add.pop("category", "datapoint")
    default = {"id": id_, "label": id_}
    if category == "datapoint":
        default = {**default, "rir_field_names": [], **_new_singlevalue(datapoint_to_add)}
    elif category == "multivalue":
        default = {
            **default,
            "children": None,
            "default_value": None,
            "min_occurrences": None,
            "max_occurrences": None,
        }
    elif category == "tuple":
        default = {**default, "rir_field_names": [], "children": []}
    elif category == "section":
        raise click.BadArgumentUsage("Cannot add section.")
    else:
        raise click.BadArgumentUsage("Unknown category.")
    return {**default, **datapoint_to_add, "category": category}


def _new_singlevalue(datapoint_to_add: DataPointDict) -> DataPointDict:
    type_ = datapoint_to_add.pop("type", "string")
    default: DataPointDict = {
        "width_chars": 10,
        "default_value": None,
        "constraints": {"required": False},
    }
    if type_ == "enum":
        default = {**default, "options": [{"value": "0", "label": "---"}]}
    elif type_ == "date":
        default = {**default, "format": "D. M. YYYY"}
    elif type_ == "number":
        default = {**default, "format": "# ##0.#"}
    elif type_ != "string":
        raise click.BadArgumentUsage("Unknown type.")

    return {**default, "type": type_}
