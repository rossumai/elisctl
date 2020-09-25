import json
import re
from functools import partial
from traceback import print_tb
from unittest import mock

import pytest
from itertools import chain
from requests import Request
from requests_mock.response import _Context

from rossumctl.user import change_command, create_command, delete_command, list_command
from tests import SuperDictOf
from tests.conftest import (
    API_URL,
    GROUPS_URL,
    ORGANIZATIONS_URL,
    QUEUES_URL,
    TOKEN,
    USERS_URL,
    WORKSPACES_URL,
    match_uploaded_json,
)

NEW_USERNAME = "test_username@example.com"

ORGANIZATION_ID = "1"
ORGANIZATION_URL = f"{ORGANIZATIONS_URL}/{ORGANIZATION_ID}"
WORKSPACES = QUEUES = ["1", "2"]


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestCreate:
    @pytest.mark.usefixtures("mock_user_urls", "mock_organization_urls")
    @mock.patch("rossumctl.user.generate_secret")
    def test_create(self, mock_password, requests_mock, cli_runner):
        mock_password.return_value = generated_password = "secret" * 2
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
                    "queues": [],
                    "ui_settings": {"locale": "en"},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": new_user_id},
        )
        result = cli_runner.invoke(create_command, [NEW_USERNAME, "-q", 12345])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{new_user_id}, {generated_password}\n" == result.output

    @pytest.mark.usefixtures("mock_user_urls", "mock_organization_urls")
    def test_queues_specified(self, requests_mock, cli_runner):
        requests_mock.post(
            USERS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                SuperDictOf({"queues": [f"{QUEUES_URL}/{q_id}" for q_id in QUEUES]}),
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": 1},
        )
        result = cli_runner.invoke(
            create_command, [NEW_USERNAME] + list(chain.from_iterable(("-q", q) for q in QUEUES))
        )
        assert not result.exit_code, print_tb(result.exc_info[2])

    def test_queues_not_specified(self, cli_runner):
        result = cli_runner.invoke(create_command, [NEW_USERNAME])
        assert result.exit_code == 2
        assert 'Error: Missing option "-q" / "--queue-id".' in result.output.replace("'", '"')

    @pytest.mark.usefixtures("mock_user_urls")
    def test_create_in_organization(self, requests_mock, cli_runner):
        organization_id = 2
        organization_url = f"{ORGANIZATIONS_URL}/{organization_id}"
        requests_mock.get(
            organization_url,
            json={"url": organization_url, "id": organization_id},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            USERS_URL,
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": 1},
            additional_matcher=partial(
                match_uploaded_json, SuperDictOf({"organization": organization_url})
            ),
        )
        result = cli_runner.invoke(
            create_command, [NEW_USERNAME, "-o", organization_id, "-q", 12345]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])

    @pytest.mark.usefixtures("mock_user_urls", "mock_organization_urls")
    def test_weak_password(self, requests_mock, cli_runner):
        error_json = {
            "password": [
                "This password is too short. It must contain at least 8 characters.",
                "This password is too common.",
            ]
        }
        weak_password = "secret"
        requests_mock.post(
            USERS_URL,
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=400,
            additional_matcher=partial(
                match_uploaded_json, SuperDictOf({"password": weak_password})
            ),
            json=error_json,
        )
        result = cli_runner.invoke(create_command, [NEW_USERNAME, "-p", weak_password, "-q", 12345])
        assert result.exit_code == 1, print_tb(result.exc_info[2])
        assert result.output == f"Error: Invalid response [{USERS_URL}]: {json.dumps(error_json)}\n"

    def test_user_exists(self, requests_mock, cli_runner):
        requests_mock.get(
            USERS_URL + f"?username={NEW_USERNAME}",
            complete_qs=True,
            json={"pagination": {"total": 1, "next": None}, "results": [{}]},
        )
        result = cli_runner.invoke(create_command, [NEW_USERNAME, "-q", 12345])
        assert result.exit_code == 1
        assert result.output == f"Error: User with username {NEW_USERNAME} already exists.\n"


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestList:
    def test_success(self, requests_mock, cli_runner):
        user_id = 1
        username = "test@example.com"
        group_name = "test"
        queue_id = 1

        queue_url = f"{QUEUES_URL}/{queue_id}"
        group_url = f"{GROUPS_URL}/1"

        requests_mock.get(
            USERS_URL + f"?is_active=true",
            complete_qs=True,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [
                    {
                        "id": user_id,
                        "groups": [group_url],
                        "queues": [queue_url],
                        "username": username,
                    }
                ],
            },
        )
        requests_mock.get(
            QUEUES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": queue_id, "url": queue_url}],
            },
        )
        requests_mock.get(
            GROUPS_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"name": group_name, "url": group_url}],
            },
        )

        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  username          groups      queues
----  ----------------  --------  --------
   {user_id}  {username}  {group_name}             {queue_id}
"""
        assert result.output == expected_table


@pytest.mark.usefixtures("mock_login_request", "mock_user_urls", "rossum_credentials")
class TestChange:
    def test_success(self, requests_mock, cli_runner):
        queue_id = "1"
        locale = "cs"
        data = {
            "queues": [f"{QUEUES_URL}/{queue_id}"],
            "groups": [f"{GROUPS_URL}/2"],
            "ui_settings": {"locale": locale},
            "password": "new_password",
        }
        user_id = "1"

        requests_mock.get(f"{USERS_URL}/{user_id}", json={"ui_settings": {}})
        requests_mock.patch(
            f"{USERS_URL}/{user_id}", additional_matcher=partial(match_uploaded_json, data)
        )

        result = cli_runner.invoke(
            change_command,
            [user_id, "-q", queue_id, "-g", "admin", "-l", locale, "-p", data["password"]],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_noop(self, requests_mock, cli_runner):
        cli_runner.invoke(change_command, ["1"])
        assert not requests_mock.called


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestDelete:
    def test_success(self, requests_mock, cli_runner):
        user_id = "1"
        requests_mock.patch(
            f"{USERS_URL}/{user_id}",
            additional_matcher=partial(match_uploaded_json, {"is_active": False}),
        )

        result = cli_runner.invoke(delete_command, [user_id, "--yes"])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output


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
        QUEUES_URL,
        json={
            "results": [{"url": f"{QUEUES_URL}/{q}", "id": int(q)} for q in QUEUES],
            "pagination": {"next": None, "total": 1},
        },
    )

    requests_mock.get(
        re.compile(fr"{WORKSPACES_URL}\?organization=\d"),
        json={
            "results": [
                {"url": f"{WORKSPACES_URL}/{w}", "queues": [f"{QUEUES_URL}/{w}"]}
                for w in WORKSPACES
            ],
            "pagination": {"next": None, "total": 1},
        },
    )

    requests_mock.get(
        f"{GROUPS_URL}?name=annotator",
        json={"results": [{"url": f"{GROUPS_URL}/1"}], "pagination": {"next": None, "total": 1}},
        request_headers={"Authorization": f"Token {TOKEN}"},
        complete_qs=True,
    )

    requests_mock.get(
        f"{GROUPS_URL}?name=admin",
        json={"results": [{"url": f"{GROUPS_URL}/2"}], "pagination": {"next": None, "total": 1}},
        request_headers={"Authorization": f"Token {TOKEN}"},
        complete_qs=True,
    )

    requests_mock.get(
        USERS_URL + f"?username={NEW_USERNAME}",
        complete_qs=True,
        json={"pagination": {"total": 0, "next": None}, "results": []},
    )

    requests_mock.get(f"{API_URL}/v1/auth/user", json={"url": f"{USERS_URL}/1"})


@pytest.fixture
def mock_organization_urls(requests_mock):
    requests_mock.get(
        ORGANIZATION_URL,
        json={"url": ORGANIZATION_URL, "id": ORGANIZATION_ID},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )

    requests_mock.get(f"{USERS_URL}/1", json={"organization": ORGANIZATION_URL})

    requests_mock.get(
        re.compile(fr"{WORKSPACES_URL}/\d$"),
        json={"organization": ORGANIZATION_URL},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )
