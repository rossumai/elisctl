#!/usr/bin/env python3
import datetime
import json
from io import StringIO

import click as click
import pandas as pd
import requests
from math import ceil

from tools.lib.api_client import APIClient

now = datetime.datetime.utcnow()
FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
]


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def cli(ctx: click.Context) -> None:
    pass


@cli.command(name="csv")
@click.pass_context
@click.option(
    "--start",
    default=str(now - datetime.timedelta(days=1)),
    type=click.DateTime(FORMATS),  # type: ignore
)
@click.option("--stop", default=str(now), type=click.DateTime(FORMATS))  # type: ignore
@click.option("--step", "float_step", default=0.1, type=float, help="Step in days")
def csv(
    ctx: click.Context, start: datetime.datetime, stop: datetime.datetime, float_step: float
) -> None:
    api_client = APIClient.csv()

    step = datetime.timedelta(days=float_step)
    dfs = []
    while stop > start:
        start += step
        rsp = api_client.get(f"byperiod/{ceil(step.total_seconds())}/{int(start.timestamp())}")
        assert isinstance(rsp, str)
        dfs.append(pd.read_csv(StringIO(rsp), sep=";"))

    df = pd.concat(dfs)
    with StringIO() as buffer:
        df.to_csv(buffer, sep=";", index=False)
        click.echo(buffer.getvalue())


@cli.command(name="schema")
@click.pass_context
@click.argument("id_", metavar="ID", type=str)
@click.option("--indent", default=2, type=int)
@click.option("--ensure-ascii", is_flag=True, type=bool)
def schema(ctx: click.Context, id_: str, indent: int, ensure_ascii: bool):
    with APIClient() as api_client:
        schema_dict = api_client.get(f"schemas/{id_}")
    assert isinstance(schema_dict, dict)
    click.echo(
        json.dumps(schema_dict["content"], indent=indent, ensure_ascii=ensure_ascii, sort_keys=True)
    )


if __name__ == "__main__":
    cli()
