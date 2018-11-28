#!/usr/bin/env python3
from io import StringIO
from typing import Optional

import click as click
import pandas as pd


@click.command()
@click.argument("xls", type=click.File("rb"))
@click.option("--value", default=0, type=int)
@click.option("--label", default=1, type=int)
@click.option("--sheet", default=0, type=int)
@click.option("--header", default=None, type=int)
def cli(xls: click.File, label: str, value: str, sheet: int, header: Optional[int]) -> None:
    df = pd.read_excel(
        xls,
        sheet_name=sheet,
        usecols=[value, label],
        names=["value", "label"],
        dtype=(str, str),
        header=header,
    )
    with StringIO() as buffer:
        df.to_csv(buffer, header=False, sep=";", index=False)
        click.echo(buffer.getvalue())


if __name__ == "__main__":
    cli()
