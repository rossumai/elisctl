#!/usr/bin/env python3
import datetime
from io import StringIO

import click as click
import pandas as pd
from math import ceil

from elisctl.lib.api_client import APIClient, get_text

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


@click.group("csv")
@click.pass_context
def cli(ctx: click.Context) -> None:
    pass


@cli.command(name="get", help="Download a large CSV in chunks.")
@click.pass_context
@click.option(
    "--start",
    default=str(now - datetime.timedelta(days=1)),
    type=click.DateTime(FORMATS),  # type: ignore
)
@click.option("--stop", default=str(now), type=click.DateTime(FORMATS))  # type: ignore
@click.option("--step", "float_step", default=0.1, type=float, help="Step in days")
def download_command(
    ctx: click.Context, start: datetime.datetime, stop: datetime.datetime, float_step: float
) -> None:
    api_client = APIClient.csv(context=ctx.obj)

    step = datetime.timedelta(days=float_step)
    dfs = []
    while stop > start:
        start += step
        rsp = api_client.get(f"byperiod/{ceil(step.total_seconds())}/{int(start.timestamp())}")
        dfs.append(pd.read_csv(StringIO(get_text(rsp)), sep=";"))

    df = pd.concat(dfs)
    with StringIO() as buffer:
        # set line_terminator to ensure universal newline support for all the OS
        df.to_csv(buffer, sep=";", index=False, line_terminator="\n")
        click.echo(buffer.getvalue())


if __name__ == "__main__":
    cli()
