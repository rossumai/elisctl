import json
import re
from functools import partial
from traceback import print_tb
from typing import List

from click.testing import CliRunner
from requests import Request

from tests.conftest import API_URL, TOKEN
from tools import upload

DATA = """\
1;abc
2;cde
3;fgh\
"""
USERNAME = "something"
PASSWORD = "secret"
SCHEMA_NAME = "schema.json"
schema_content: List = []
schema_id = "1"


class TestUpload:
    def test_schema_create(self, mock_login_request, mock_get_schema, requests_mock):
        new_schema = {"content": schema_content, "name": "test"}
        new_schema_id = "2"
        schemas_url = f"{API_URL}/v1/schemas"
        new_schema_url = f"{schemas_url}/{new_schema_id}"

        requests_mock.post(
            schemas_url,
            json={"url": new_schema_url, "queues": [], **new_schema},
            additional_matcher=partial(_match_uploaded_json, new_schema),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
        )
        requests_mock.patch(
            re.compile(fr"{API_URL}/v1/queues/\d"),
            request_headers={"Authorization": f"Token {TOKEN}"},
            additional_matcher=partial(_match_uploaded_json, {"schema": new_schema_url}),
        )

        runner = CliRunner(
            env={
                "ADMIN_API_URL": API_URL,
                "ADMIN_API_LOGIN": USERNAME,
                "ADMIN_API_PASSWORD": PASSWORD,
            }
        )
        with runner.isolated_filesystem():
            with open(SCHEMA_NAME, "w") as schema:
                json.dump(schema_content, schema)
            result = runner.invoke(upload.cli, [SCHEMA_NAME, "schema", schema_id])
        assert not result.exit_code, print_tb(result.exc_info[2])

    def test_schema_rewrite(self, mock_login_request, requests_mock):
        schemas_url = f"{API_URL}/v1/schemas"
        schema_url = f"{schemas_url}/{schema_id}"

        requests_mock.patch(
            schema_url,
            additional_matcher=partial(_match_uploaded_json, {"content": schema_content}),
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        runner = CliRunner(
            env={
                "ADMIN_API_URL": API_URL,
                "ADMIN_API_LOGIN": USERNAME,
                "ADMIN_API_PASSWORD": PASSWORD,
            }
        )
        with runner.isolated_filesystem():
            with open(SCHEMA_NAME, "w") as schema:
                json.dump(schema_content, schema)
            result = runner.invoke(upload.cli, [SCHEMA_NAME, "schema", schema_id, "--rewrite"])
        assert not result.exit_code, print_tb(result.exc_info[2])


def _match_uploaded_json(uploaded_json: dict, request: Request) -> bool:
    return request.json() == uploaded_json
