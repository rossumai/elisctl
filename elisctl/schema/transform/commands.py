import json

from typing import Optional, IO, Tuple

import click as click

from elisctl import option, argument
from elisctl.lib import DataPoints, DataPointDict
from . import (
    traverse_datapoints,
    substitute_options,
    remove,
    wrap_in_multivalue,
    add,
    _new_datapoint,
    change,
    get,
)


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
@argument.id_(type=str)
@click.argument("new_options", type=click.File("rb"))
def substitute_options_command(ctx: click.Context, new_options: IO[str], id_: str) -> DataPoints:
    options_dict = json.load(new_options)
    return traverse_datapoints(ctx.obj["SCHEMA"], substitute_options, id_=id_, options=options_dict)


@cli.command(name="remove", help="Remove datapoints.")
@click.pass_context
@argument.schema_file
@click.argument("ids", nargs=-1, type=str)
def remove_command(ctx: click.Context, ids: Tuple[str, ...]) -> DataPoints:
    return traverse_datapoints(ctx.obj["SCHEMA"], remove, ids=ids)


@cli.command(
    name="wrap-in-multivalue",
    short_help="Put all datapoints into a multivalue.",
    help="Put all datapoints into a multivalue (unless they are already in a multivalue).",
)
@click.pass_context
@argument.schema_file
@click.argument("exclude_ids", nargs=-1, type=str)
def wrap_in_multivalue_command(ctx: click.Context, exclude_ids: Tuple[str, ...]) -> DataPoints:
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
@argument.datapoint_parameters
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
    datapoint_parameters: DataPointDict,
    place_before: Optional[str],
) -> DataPoints:

    return traverse_datapoints(
        ctx.obj["SCHEMA"],
        add,
        parent_id=parent_id,
        datapoint_to_add=_new_datapoint(datapoint_parameters),
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
@argument.id_(type=str)
@argument.datapoint_parameters
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
    ctx: click.Context, id_: str, datapoint_parameters: DataPointDict, categories: Tuple[str]
) -> DataPoints:
    return traverse_datapoints(
        ctx.obj["SCHEMA"],
        change,
        id_=id_,
        to_change=datapoint_parameters,
        filtered_categories=categories,
    )


@cli.command(name="move", help="Move datapoint to new parent datapoint.")
@click.pass_context
@argument.schema_file
@click.argument("source_id", type=str)
@click.argument("target_id", type=str)
def move_command(ctx: click.Context, source_id: str, target_id: str) -> DataPoints:
    source_dp = get(ctx.obj["SCHEMA"], id_=source_id)
    new_schema = traverse_datapoints(ctx.obj["SCHEMA"], remove, ids=(source_id,))
    return traverse_datapoints(new_schema, add, parent_id=target_id, datapoint_to_add=source_dp)


@cli.resultcallback()
@click.pass_context
def process_result(
    ctx: click.Context,
    result: DataPoints,
    indent: int,
    ensure_ascii: bool,
    sort_keys: bool,
    output_file: Optional[IO[str]],
) -> None:
    output = json.dumps(result, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys)
    click.echo(output.encode("utf-8"), file=output_file, nl=False)
