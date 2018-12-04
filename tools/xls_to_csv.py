#!/usr/bin/env python3
from io import StringIO
from typing import Optional

import click as click
import pandas as pd


@click.command(help="Converts an Excel sheet to a CSV. All indices are 0-based.")
@click.argument("xls", type=click.File("rb"))
@click.option("--value", default=0, type=int, help="Index of column with values")
@click.option("--label", default=1, type=int, help="Index of column with labels")
@click.option("--sheet", default=0, type=int, help="Index of sheet")
@click.option(
    "--header",
    default=None,
    type=int,
    help="Index of header row. If not chosen, no header is assumed. "
    "(skiprows are applied before header lookup)",
)
@click.option("--skiprows", default="", type=str, help="Indices of rows to skip")
def cli(
    xls: click.File, label: int, value: int, sheet: int, skiprows: str, header: Optional[int]
) -> None:
    try:
        skiprows_list = [int(r.strip()) for r in skiprows.split(",") if r]
    except ValueError as e:
        raise click.BadArgumentUsage('skiprows: Expecting list of ints delimited by ",".') from e

    df = pd.read_excel(
        xls,
        sheet_name=sheet,
        usecols=[value, label],
        names=["value", "label"],
        dtype=(str, str),
        header=header,
        skiprows=skiprows_list,
    )
    with StringIO() as buffer:
        df.to_csv(buffer, header=False, sep=";", index=False)
        click.echo(buffer.getvalue())


if __name__ == "__main__":
    cli()
