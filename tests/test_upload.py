import json
import re
from functools import partial
from traceback import print_tb
from typing import List

import pytest

from rossumctl.schema.upload import upload_command
from tests.conftest import TOKEN, match_uploaded_json, SCHEMAS_URL, QUEUES_URL

DATA = """\
1;abc
2;cde
3;fgh\
"""
SCHEMA_NAME = "schema.json"
schema_content: List = []
schema_id = "1"


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestUpload:
    @pytest.mark.usefixtures("mock_get_schema")
    def test_schema_create(self, requests_mock, isolated_cli_runner):
        new_schema = {"content": schema_content, "name": "test"}
        new_schema_id = "2"
        new_schema_url = f"{SCHEMAS_URL}/{new_schema_id}"

        requests_mock.post(
            SCHEMAS_URL,
            json={"url": new_schema_url, "queues": [], **new_schema},
            additional_matcher=partial(match_uploaded_json, new_schema),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
        )
        requests_mock.patch(
            re.compile(fr"{QUEUES_URL}/\d"),
            request_headers={"Authorization": f"Token {TOKEN}"},
            additional_matcher=partial(match_uploaded_json, {"schema": new_schema_url}),
        )

        with open(SCHEMA_NAME, "w") as schema:
            json.dump(schema_content, schema)
        result = isolated_cli_runner.invoke(upload_command, [schema_id, SCHEMA_NAME])
        assert not result.exit_code, print_tb(result.exc_info[2])

    def test_schema_rewrite(self, requests_mock, isolated_cli_runner):
        schema_url = f"{SCHEMAS_URL}/{schema_id}"

        requests_mock.patch(
            schema_url,
            additional_matcher=partial(match_uploaded_json, {"content": schema_content}),
            request_headers={"Authorization": f"Token {TOKEN}"},
        )
        with open(SCHEMA_NAME, "w") as schema:
            json.dump(schema_content, schema)
        result = isolated_cli_runner.invoke(upload_command, [schema_id, SCHEMA_NAME, "--rewrite"])
        assert not result.exit_code, print_tb(result.exc_info[2])
