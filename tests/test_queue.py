from functools import partial
from traceback import print_tb

import pytest

from elisctl.queue import create_command
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


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestCreate:
    def test_success(self, requests_mock, cli_runner):
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
                {"name": name, "workspace": WORKSPACE_URL, "schema": SCHEMA_URL},
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": new_id},
        )
        result = cli_runner.invoke(create_command, [name])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{new_id}, no email-prefix specified\n" == result.output
