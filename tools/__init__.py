import click

from tools import compare, csv_to_options, transform_schema, download, upload, xls_to_csv


@click.group("elisctl", context_settings={"help_option_names": ["-h", "--help"]})
def entry_point() -> None:
    pass


entry_point.add_command(compare.cli)
entry_point.add_command(csv_to_options.cli)
entry_point.add_command(xls_to_csv.cli)
entry_point.add_command(transform_schema.cli)
entry_point.add_command(download.cli)
entry_point.add_command(upload.cli)
