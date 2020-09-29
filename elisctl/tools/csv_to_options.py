#!/usr/bin/env python3
from typing import Optional, IO

import click as click
import pandas as pd

from elisctl import option

HELP = "Create options list from csv. Usable for filling options key of enum datapoint in schema."


@click.command("csv_to_options", help=HELP)
@click.argument("csv", type=click.File("rb"))
@click.option("--delimiter", default=";", type=str)
@click.option("--header", default=None, type=int)
@click.option("--add-value", is_flag=True)
@click.option("--empty-value", default=None, type=str)
@option.output_file
def cli(
    csv: click.File,
    header: Optional[int],
    delimiter: str,
    add_value: bool,
    empty_value: Optional[str],
    output_file: Optional[IO[str]],
) -> None:
    names = ["value", "label"] if header is None else None
    df = pd.read_csv(csv, sep=delimiter, names=names, header=header, dtype=(str, str))
    if add_value:
        df.label = df.apply(": ".join, axis=1)
    if empty_value is not None:
        null_df = pd.DataFrame([[empty_value, "-" * 3]], columns=["value", "label"])
        df = pd.concat([null_df, df])
    click.echo(df.to_json(orient="records").encode("utf-8"), file=output_file, nl=False)
