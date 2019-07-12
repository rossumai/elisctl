import json
import re
from typing import Optional, Tuple

import click
import jmespath
from typing.io import IO

from elisctl.lib.api_client import ELISClient, get_json, get_text
from elisctl import option


@click.command(name="extract", help="Upload documents and extract data from them.")
@click.argument("queue_id", metavar="QUEUE_ID", type=str)
@click.argument(
    "files", metavar="FILE_TO_UPLOAD", nargs=-1, type=click.Path(readable=True), required=True
)
@click.option(
    "--format",
    "format_",
    default="json",
    type=click.Choice(["json", "csv", "xml"]),
    help="Format of the output file.",
)
@option.output_file
@click.option("--indent", default=4, type=int, help="Set indentation for JSON output file.")
@click.option(
    "--ensure-ascii",
    is_flag=True,
    type=bool,
    help="Ensure that the output file is in valid ASCII characters.",
)
@click.pass_context
def get_data(
    ctx: click.Context,
    queue_id: int,
    files: Tuple[str],
    indent: int,
    ensure_ascii: bool,
    format_: str,
    output_file: Optional[IO[str]],
):
    annotations_to_export = list()

    with ELISClient(context=ctx.obj) as elis:
        for file in files:
            json_response = elis.upload_document(queue_id, file)
            annotation_id = get_id(json_response)
            annotations_to_export.append(annotation_id)
            elis.poll_annotation(annotation_id, _is_done)

        export_data = elis.export_data(queue_id, annotations_to_export, format_)

        if format_ == "json":
            output = json.dumps(get_json(export_data), indent=indent, ensure_ascii=ensure_ascii)
        else:
            output = get_text(export_data)
        click.echo(output.encode("utf-8"), file=output_file, nl=False)


def get_id(json_response: dict) -> int:
    annotation_url = jmespath.search("results[*].annotation | [0]", json_response)
    annotation_id = re.search(r"(?<=annotations/)\d*$", annotation_url)
    if annotation_id is not None:
        annotation_id_number = int(annotation_id.group())
        return annotation_id_number
    raise click.ClickException("Could not get annotation ID from the response.")


def _is_done(response):
    return response["status"] != "importing"
