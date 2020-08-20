from unittest import mock

import click
import io
import pytest
from pathlib import Path

from rossumctl.common import schema_content_factory
from rossumctl.schema.xlsx import XlsxToSchema


def file_decorator(*_args, **_kwargs):
    def test_decorator(f):
        def test_wrapped(*args, **kwargs):
            return f(*args, **kwargs)

        return test_wrapped

    return test_decorator


parameter = schema_content_factory(file_decorator)


class TestSchemaContent:
    def test_json(self):
        command = mock.Mock()

        with io.BytesIO(b"{}") as buffer:
            parameter(command)(schema_content_file_=buffer)
        command.assert_called_once_with(schema_content={})

    def test_xlsx(self):
        command = mock.Mock()

        with io.BytesIO(b"<mock xlsx>") as buffer, mock.patch.object(
            XlsxToSchema,
            "convert",  # convert tested in test_schema_xlsx.test_xlsx_loaded_correctly
            return_value={},
        ):
            parameter(command)(schema_content_file_=buffer)
        command.assert_called_once_with(schema_content={})

    def test_error(self, tmp_path: Path):
        command = mock.Mock()
        invalid_file = tmp_path / "invalid"
        invalid_file.write_bytes(b"invalid")

        with invalid_file.open() as buffer, pytest.raises(click.ClickException) as e:
            parameter(command)(schema_content_file_=buffer)
        assert e.value.args[0] == (
            f"File {invalid_file} could not be loaded."
            "\n\tJSON: Expecting value: line 1 column 1 (char 0)"
            "\n\tXLSX: File is not a zip file"
        )
        command.assert_not_called()

    def test_none(self):
        command = mock.Mock()
        parameter(command)(schema_content_file_=None)
        command.assert_called_once_with(schema_content=None)
