import re
from functools import partial
from traceback import print_tb
from unittest import mock

import pytest
from requests import Request
from requests_mock.response import _Context

from tests.conftest import API_URL, TOKEN, match_uploaded_json
from elisctl.user.create import create_command

USERNAME = "test_user@rossum.ai"
PASSWORD = "secret"


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestUser:
    QUEUES = ["1", "2"]
    new_username = "test_username@example.com"

    users_url = f"{API_URL}/v1/users"

    @mock.patch("elisctl.user.create._generate_password")
    def test_create(self, mock_password, requests_mock, cli_runner):
        mock_password.return_value = generated_password = PASSWORD * 2
        new_user_id = 1

        queues_url = f"{API_URL}/v1/queues"
        workspaces_url = f"{API_URL}/v1/workspaces"
        groups_url = f"{API_URL}/v1/groups"
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

        requests_mock.get(
            self.users_url + f"?username={self.new_username}",
            complete_qs=True,
            json={"pagination": {"total": 0}},
        )
        requests_mock.post(
            self.users_url,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "username": self.new_username,
                    "email": self.new_username,
                    "organization": organization_url,
                    "password": generated_password,
                    "groups": [f"{groups_url}/1"],
                    "queues": [f"{queues_url}/{q_id}" for q_id in self.QUEUES],
                    "ui_settings": {"locale": "en"},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": new_user_id},
        )
        result = cli_runner.invoke(create_command, [self.new_username, *self.QUEUES])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{new_user_id}, {generated_password}\n" == result.output

    def test_user_exists(self, requests_mock, cli_runner):
        requests_mock.get(
            self.users_url + f"?username={self.new_username}",
            complete_qs=True,
            json={"pagination": {"total": 1}},
        )
        result = cli_runner.invoke(create_command, [self.new_username, *self.QUEUES])
        assert result.exit_code == 1
        assert result.output == f"Error: User with username {self.new_username} already exists.\n"


def _get_queue_json_callback(request: Request, context: _Context) -> dict:
    url = request.url
    _, id_ = url.rsplit("/", 1)
    return {"url": url, "workspace": f"{API_URL}/v1/workspaces/{id_}"}
