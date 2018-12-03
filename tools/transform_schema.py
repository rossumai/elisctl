#!/usr/bin/env python3
from __future__ import annotations

import json
import warnings
from contextlib import suppress
from copy import deepcopy
from typing import List, Callable, Optional, IO, Tuple, Iterable, Dict, Union, Iterator, Set

import click as click


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.argument("schema", type=click.File("rb"))
@click.option("--indent", default=2, type=int)
@click.option("--ensure-ascii", is_flag=True, type=bool)
def cli(ctx: click.Context, schema: IO[str], indent: int, ensure_ascii: bool) -> None:
    ctx.obj = {"SCHEMA": json.load(schema), "INDENT": indent, "ENSURE_ASCII": ensure_ascii}


@cli.command(name="substitute-options")
@click.pass_context
@click.argument("options", type=click.File("rb"))
@click.option("--id", "id_", type=str)
def substitute_options_command(ctx: click.Context, options: IO[str], id_: str) -> None:
    options_dict = json.load(options)

    new_schema = traverse_schema(
        ctx.obj["SCHEMA"], substitute_options, id_=id_, options=options_dict
    )
    click.echo(
        json.dumps(new_schema, indent=ctx.obj["INDENT"], ensure_ascii=ctx.obj["ENSURE_ASCII"])
    )


@cli.command(name="remove")
@click.pass_context
@click.argument("ids", nargs=-1, type=str)
def remove_command(ctx: click.Context, ids: Tuple[str, ...]) -> None:
    new_schema = traverse_schema(ctx.obj["SCHEMA"], remove, ids=ids)
    click.echo(
        json.dumps(new_schema, indent=ctx.obj["INDENT"], ensure_ascii=ctx.obj["ENSURE_ASCII"])
    )


@cli.command(name="wrap-in-multivalue")
@click.pass_context
@click.argument("exclude_ids", nargs=-1, type=str)
def wrap_in_multivalue_command(ctx: click.Context, exclude_ids: Tuple[str, ...]) -> None:
    new_schema = traverse_schema(
        ctx.obj["SCHEMA"], wrap_in_multivalue, exclude_ids=set(exclude_ids)
    )
    click.echo(
        json.dumps(new_schema, indent=ctx.obj["INDENT"], ensure_ascii=ctx.obj["ENSURE_ASCII"])
    )


@cli.command(name="add")
@click.pass_context
@click.argument("parent_id", type=str)
@click.argument("datapoint_parameters", nargs=-1, type=str)
def add_command(ctx: click.Context, parent_id: str, datapoint_parameters: Iterable[str]) -> None:
    try:
        datapoint_parameters_dict = dict(_split_datapoint_params(datapoint_parameters))
    except ValueError as e:
        raise click.BadArgumentUsage("Expecting <key>=<value> pairs.") from e

    new_schema = traverse_schema(
        ctx.obj["SCHEMA"],
        add,
        parent_id=parent_id,
        datapoint_to_add=_new_datapoint(datapoint_parameters_dict),
    )
    click.echo(
        json.dumps(new_schema, indent=ctx.obj["INDENT"], ensure_ascii=ctx.obj["ENSURE_ASCII"])
    )


@cli.command(name="change")
@click.pass_context
@click.argument("id_", metavar="id", type=str)
@click.argument("datapoint_parameters", nargs=-1, type=str)
def change_command(ctx: click.Context, id_: str, datapoint_parameters: Iterable[str]) -> None:
    try:
        datapoint_parameters_dict = dict(_split_datapoint_params(datapoint_parameters))
    except ValueError as e:
        raise click.BadArgumentUsage("Expecting <key>=<value> pairs.") from e

    new_schema = traverse_schema(
        ctx.obj["SCHEMA"], change, id_=id_, to_change=datapoint_parameters_dict
    )
    click.echo(
        json.dumps(new_schema, indent=ctx.obj["INDENT"], ensure_ascii=ctx.obj["ENSURE_ASCII"])
    )


def traverse_schema(schema: List[dict], transformation: Callable, **kwargs) -> List[dict]:
    new_schema = []
    for section in schema:
        new_section = deepcopy(section)

        children = new_section.pop("children", [])
        new_section["children"] = traverse_datapoints(
            children, transformation, ["section"], **kwargs
        )
        new_section = transformation(new_section, [], **kwargs)
        if new_section:
            new_schema.append(new_section)

    return new_schema


def traverse_datapoints(
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
            if datapoint["category"] == "multivalue":
                [new_datapoint["children"]] = traverse_datapoints(
                    [children], transformation, parent_categories_, **kwargs
                )
            else:
                new_datapoint["children"] = traverse_datapoints(
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
        or datapoint["category"] in ("multivalue", "section")
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
    datapoint: dict, parent_categories: List[str], parent_id: str, datapoint_to_add: dict
) -> dict:
    if datapoint["id"] != parent_id:
        return datapoint

    if datapoint["category"] in ("tuple", "section"):
        new_datapoint = deepcopy(datapoint)
        new_datapoint["children"].append(datapoint_to_add)
        return new_datapoint
    elif datapoint["category"] == "multivalue":
        warnings.warn("Cannot add child to a multivalue.")
        return datapoint
    else:
        return datapoint


def change(datapoint: dict, parent_categories: List[str], id_: str, to_change: dict) -> dict:
    if datapoint["id"] != id_:
        return datapoint
    else:
        return {**datapoint, **to_change}


def _new_datapoint(datapoint_to_add: DataPointDict) -> DataPointDict:  # noqa: F821
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


def _new_singlevalue(datapoint_to_add: DataPointDict) -> DataPointDict:  # noqa: F821
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


def _split_datapoint_params(
    datapoint_parameters: Iterable[str]
) -> Iterator[Tuple[str, DataPointDictItem]]:  # noqa: F821
    for param in datapoint_parameters:
        key, value = param.split("=", 1)
        with suppress(ValueError):
            value = json.loads(value)
        yield key, value


DataPointDictItem = Union[str, int, dict, None, list]
DataPointDict = Dict[str, DataPointDictItem]


if __name__ == "__main__":
    cli()
