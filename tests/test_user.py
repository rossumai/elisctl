import re
from functools import partial
from traceback import print_tb

import pytest
from requests import Request
from requests_mock.response import _Context

from tests.conftest import API_URL, TOKEN, match_uploaded_json
from tools.user.create import create_command


class TestUser:
    USERNAME = "test_user@rossum.ai"
    PASSWORD = "secret"
    QUEUES = ["1", "2"]

    @pytest.mark.runner_setup(
        env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
    )
    @pytest.mark.usefixtures("mock_login_request")
    def test_create(self, requests_mock, cli_runner):
        queues_url = f"{API_URL}/v1/queues"
        workspaces_url = f"{API_URL}/v1/workspaces"
        groups_url = f"{API_URL}/v1/groups"
        users_url = f"{API_URL}/v1/users"
        organization_url = f"{API_URL}/v1/organizations/1"

        requests_mock.get(
            re.compile(fr"{queues_url}/\d$"),
            json=_get_queue_json_callback,
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.get(
            re.compile(fr"{workspaces_url}/\d$"),
            json={"organization": organization_url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.get(
            f"{groups_url}?name=annotator",
            json={"results": [{"url": f"{groups_url}/1"}]},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            users_url,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "username": self.USERNAME,
                    "email": self.USERNAME,
                    "organization": organization_url,
                    "password": self.PASSWORD,
                    "groups": [f"{groups_url}/1"],
                    "queues": [f"{queues_url}/{q_id}" for q_id in self.QUEUES],
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
        )
        result = cli_runner.invoke(create_command, [self.USERNAME, self.PASSWORD, *self.QUEUES])
        assert not result.exit_code, print_tb(result.exc_info[2])


def _get_queue_json_callback(request: Request, context: _Context) -> dict:
    url = request.url
    _, id_ = url.rsplit("/", 1)
    return {"url": url, "workspace": f"{API_URL}/v1/workspaces/{id_}"}
