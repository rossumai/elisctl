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

NEW_USERNAME = "test_username@example.com"

QUEUES_URL = f"{API_URL}/v1/queues"
WORKSPACES_URL = f"{API_URL}/v1/workspaces"
GROUPS_URL = f"{API_URL}/v1/groups"
ORGANIZATION_URL = f"{API_URL}/v1/organizations/1"
USERS_URL = f"{API_URL}/v1/users"


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestUser:
    QUEUES = ["1", "2"]

    @pytest.mark.usefixtures("mock_user_urls")
    @mock.patch("elisctl.user.create._generate_password")
    def test_create(self, mock_password, requests_mock, cli_runner):
        mock_password.return_value = generated_password = PASSWORD * 2
        new_user_id = 1

        requests_mock.post(
            USERS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "username": NEW_USERNAME,
                    "email": NEW_USERNAME,
                    "organization": ORGANIZATION_URL,
                    "password": generated_password,
                    "groups": [f"{GROUPS_URL}/1"],
                    "queues": [f"{QUEUES_URL}/{q_id}" for q_id in self.QUEUES],
                    "ui_settings": {"locale": "en"},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": new_user_id},
        )
        result = cli_runner.invoke(create_command, [NEW_USERNAME, *self.QUEUES])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{new_user_id}, {generated_password}\n" == result.output

    def test_user_exists(self, requests_mock, cli_runner):
        requests_mock.get(
            USERS_URL + f"?username={NEW_USERNAME}",
            complete_qs=True,
            json={"pagination": {"total": 1}},
        )
        result = cli_runner.invoke(create_command, [NEW_USERNAME, *self.QUEUES])
        assert result.exit_code == 1
        assert result.output == f"Error: User with username {NEW_USERNAME} already exists.\n"


@pytest.fixture
def mock_user_urls(requests_mock):
    def _get_queue_json_callback(request: Request, context: _Context) -> dict:
        url = request.url
        _, id_ = url.rsplit("/", 1)
        return {"url": url, "workspace": f"{WORKSPACES_URL}/{id_}"}

    requests_mock.get(
        re.compile(fr"{QUEUES_URL}/\d$"),
        json=_get_queue_json_callback,
        request_headers={"Authorization": f"Token {TOKEN}"},
    )

    requests_mock.get(
        re.compile(fr"{WORKSPACES_URL}/\d$"),
        json={"organization": ORGANIZATION_URL},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )

    requests_mock.get(
        f"{GROUPS_URL}?name=annotator",
        json={"results": [{"url": f"{GROUPS_URL}/1"}]},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )

    requests_mock.get(
        USERS_URL + f"?username={NEW_USERNAME}", complete_qs=True, json={"pagination": {"total": 0}}
    )
