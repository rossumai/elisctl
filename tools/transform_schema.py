#!/usr/bin/env python3
import json
from copy import deepcopy
from typing import List, Callable

import click as click


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.argument("schema", type=click.File("rb"))
@click.option("--indent", default=2, type=int)
@click.option("--ensure-ascii", is_flag=True, type=bool)
def cli(ctx: click.Context, schema: click.File, indent: int, ensure_ascii: bool) -> None:
    ctx.obj = {"SCHEMA": json.load(schema), "INDENT": indent, "ENSURE_ASCII": ensure_ascii}


@cli.command(name="substitute-options")
@click.pass_context
@click.argument("options", type=click.File("rb"))
@click.option("--id", "id_", type=str)
def substitute_options_command(ctx: click.Context, options: click.File, id_: str) -> None:
    options_dict = json.load(options)

    new_schema = traverse_schema(
        ctx.obj["SCHEMA"], substitute_options, id_=id_, options=options_dict
    )
    click.echo(
        json.dumps(new_schema, indent=ctx.obj["INDENT"], ensure_ascii=ctx.obj["ENSURE_ASCII"])
    )


def traverse_schema(schema: List[dict], transformation: Callable, **kwargs) -> List[dict]:
    new_schema = []
    for section in schema:
        new_section = deepcopy(section)

        children = new_section.pop("children", [])
        new_section["children"] = traverse_datapoints(children, transformation, **kwargs)
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


if __name__ == "__main__":
    cli()
