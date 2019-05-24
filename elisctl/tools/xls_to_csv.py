#!/usr/bin/env python3
import operator
from io import StringIO
from typing import Optional

import click as click
import pandas as pd
from typing.io import IO

from elisctl import option


@click.command("xls_to_csv", help="Convert an Excel sheet to a CSV. All indices are 0-based.")
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
@option.output_file
def cli(
    xls: click.File,
    label: int,
    value: int,
    sheet: int,
    skiprows: str,
    header: Optional[int],
    output_file: Optional[IO[str]],
) -> None:
    try:
        skiprows_list = [int(r.strip()) for r in skiprows.split(",") if r]
    except ValueError as e:
        raise click.BadArgumentUsage('skiprows: Expecting list of ints delimited by ",".') from e
    cols = {"value": value, "label": label}
    df = pd.read_excel(
        xls,
        sheet_name=sheet,
        usecols=[value, label],
        names=[col for col, _ in sorted(cols.items(), key=operator.itemgetter(1))],
        dtype=(str, str),
        header=header,
        skiprows=skiprows_list,
    )
    df = df[list(cols.keys())]
    with StringIO() as buffer:
        df.to_csv(buffer, header=False, sep=";", index=False)
        click.echo(buffer.getvalue().encode("utf-8"), file=output_file, nl=False)
