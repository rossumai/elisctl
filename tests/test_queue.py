from functools import partial
from traceback import print_tb

import pytest

from elisctl.queue import create_command, list_command, delete_command, change_command
from tests.conftest import (
    API_URL,
    TOKEN,
    match_uploaded_json,
    WORKSPACES_URL,
    SCHEMAS_URL,
    QUEUES_URL,
)

USERNAME = "test_user@rossum.ai"
PASSWORD = "secret"
WORKSPACE_ID = "1"
WORKSPACE_URL = f"{WORKSPACES_URL}/{WORKSPACE_ID}"
SCHEMA_URL = f"{SCHEMAS_URL}/1"
SCHEMA_FILE_NAME = "schema.json"


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestCreate:
    def test_success(self, requests_mock, isolated_cli_runner):
        name = "TestName"
        new_id = "2"
        requests_mock.get(
            WORKSPACES_URL,
            json={"pagination": {"next": None, "total": 1}, "results": [{"url": WORKSPACE_URL}]},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            SCHEMAS_URL,
            additional_matcher=partial(
                match_uploaded_json, {"name": f"{name} schema", "content": []}
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"url": SCHEMA_URL},
        )
        requests_mock.post(
            QUEUES_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": name,
                    "workspace": WORKSPACE_URL,
                    "schema": SCHEMA_URL,
                    "rir_url": "https://all.rir.rossum.ai",
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": new_id},
        )

        with open(SCHEMA_FILE_NAME, "w") as schema:
            print("[]", file=schema)

        result = isolated_cli_runner.invoke(
            create_command, ["--schema-content-file", SCHEMA_FILE_NAME, name]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{new_id}, no email-prefix specified\n" == result.output


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestList:
    def test_success(self, requests_mock, cli_runner):
        queue_id = 1
        name = "TestQueue"
        workspace_id = 2

        queue_url = f"{QUEUES_URL}/{queue_id}"
        workspace_url = f"{WORKSPACES_URL}/{queue_id}"

        requests_mock.get(
            QUEUES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [
                    {"id": queue_id, "url": queue_url, "workspace": workspace_url, "name": name}
                ],
            },
        )
        requests_mock.get(
            WORKSPACES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": workspace_id, "url": workspace_url}],
            },
        )

        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  name         workspace
----  ---------  -----------
   {queue_id}  {name}            {workspace_id}
"""
        assert result.output == expected_table


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestDelete:
    def test_success(self, requests_mock, cli_runner):
        queue_id = "1"
        queue_url = f"{QUEUES_URL}/{queue_id}"

        requests_mock.get(
            queue_url,
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": queue_id, "url": queue_url},
        )

        requests_mock.delete(
            queue_url, request_headers={"Authorization": f"Token {TOKEN}"}, status_code=204
        )

        result = cli_runner.invoke(delete_command, [queue_id, "--yes"])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestChange:
    def test_success(self, requests_mock, cli_runner):
        name = "TestName"
        queue_id = "1"

        requests_mock.patch(
            f"{QUEUES_URL}/{queue_id}",
            additional_matcher=partial(match_uploaded_json, {"name": name}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )
        result = cli_runner.invoke(change_command, [queue_id, "-n", name])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output
