from typing import Optional
from unittest import mock

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
    INBOXES_URL,
    USERS_URL,
    CONNECTORS_URL,
)

USERNAME = "test_user@rossum.ai"
PASSWORD = "secret"
WORKSPACE_ID = "1"
WORKSPACE_URL = f"{WORKSPACES_URL}/{WORKSPACE_ID}"
SCHEMA_URL = f"{SCHEMAS_URL}/1"
SCHEMA_FILE_NAME = "schema.json"


class QueueFixtures:
    name: Optional[str] = None
    queue_id: Optional[str] = None

    @pytest.fixture
    def create_queue_urls(self, requests_mock):
        requests_mock.get(
            WORKSPACES_URL,
            json={"pagination": {"next": None, "total": 1}, "results": [{"url": WORKSPACE_URL}]},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            SCHEMAS_URL,
            additional_matcher=partial(
                match_uploaded_json, {"name": f"{self.name} schema", "content": []}
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"url": SCHEMA_URL},
        )

        queue_content = {
            "name": self.name,
            "workspace": WORKSPACE_URL,
            "schema": SCHEMA_URL,
            "rir_url": "https://all.rir.rossum.ai",
        }
        requests_mock.post(
            QUEUES_URL,
            additional_matcher=partial(match_uploaded_json, queue_content),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": self.queue_id, "url": self.queue_url},
        )
        requests_mock.get(
            self.queue_url, json=queue_content, request_headers={"Authorization": f"Token {TOKEN}"}
        )

    @pytest.fixture
    def create_queue_schema(self, isolated_cli_runner):
        with open(SCHEMA_FILE_NAME, "w") as schema:
            print("[]", file=schema)

    @property
    def queue_url(self) -> str:
        return f"{QUEUES_URL}/{self.queue_id}"


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestCreate(QueueFixtures):
    name = "TestName"
    queue_id = "2"

    @pytest.mark.usefixtures("create_queue_urls", "create_queue_schema")
    def test_success(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            create_command, ["--schema-content-file", SCHEMA_FILE_NAME, self.name]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{self.queue_id}, no email-prefix specified\n" == result.output

    @pytest.mark.usefixtures("create_queue_urls", "create_queue_schema")
    def test_create_inbox(self, requests_mock, isolated_cli_runner):
        email_prefix = "123456"
        bounce_mail = "test@example.com"
        email = f"{email_prefix}-aaaaaa@elis.rossum.ai"

        requests_mock.get(
            INBOXES_URL,
            json={"pagination": {"next": None, "total": 0}, "results": []},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            INBOXES_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": f"{self.name} inbox",
                    "queues": [self.queue_url],
                    "email": email,
                    "bounce_email_to": bounce_mail,
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"email": email},
        )

        with mock.patch("secrets.choice", return_value="a"):
            result = isolated_cli_runner.invoke(
                create_command,
                [
                    "--schema-content-file",
                    SCHEMA_FILE_NAME,
                    "--email-prefix",
                    email_prefix,
                    "--bounce-email",
                    bounce_mail,
                    self.name,
                ],
            )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{self.queue_id}, {email}\n" == result.output

    @pytest.mark.usefixtures("create_queue_schema")
    def test_cannot_create_inbox(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            create_command,
            ["--schema-content-file", SCHEMA_FILE_NAME, "--email-prefix", "1234567", self.name],
        )
        assert result.exit_code == 1, print_tb(result.exc_info[2])
        assert "Error: Inbox cannot be created without specified bounce email.\n" == result.output


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestList:
    def test_success(self, requests_mock, cli_runner):
        queue_id = 1
        name = "TestQueue"
        workspace_id = 2
        inbox = "test@example.com"
        inbox_url = f"{INBOXES_URL}/2"
        schema_id = 3
        schema_url = f"{SCHEMAS_URL}/{schema_id}"
        user_ids = ["4", "5"]
        user_urls = [f"{USERS_URL}/{id_}" for id_ in user_ids]
        connector_id = 2000

        queue_url = f"{QUEUES_URL}/{queue_id}"
        workspace_url = f"{WORKSPACES_URL}/{queue_id}"
        connector_url = f"{CONNECTORS_URL}/{connector_id}"

        requests_mock.get(
            QUEUES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [
                    {
                        "id": queue_id,
                        "url": queue_url,
                        "workspace": workspace_url,
                        "name": name,
                        "inbox": inbox_url,
                        "schema": schema_url,
                        "users": user_urls,
                        "connector": connector_url,
                    }
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
        requests_mock.get(
            INBOXES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"email": inbox, "url": inbox_url}],
            },
        )
        requests_mock.get(
            SCHEMAS_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": schema_id, "url": schema_url}],
            },
        )
        requests_mock.get(
            USERS_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": id_, "url": url} for id_, url in zip(user_ids, user_urls)],
            },
        )
        requests_mock.get(
            CONNECTORS_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": connector_id, "url": connector_url}],
            },
        )

        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  name         workspace  inbox               schema  users    connector
----  ---------  -----------  ----------------  --------  -------  ------------------------------------------------
   {queue_id}  {name}            {workspace_id}  {inbox}         {schema_id}  {', '.join(user_ids)}     {connector_url}
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
class TestChange(QueueFixtures):
    name = "TestName"
    queue_id = "1"

    def test_success(self, requests_mock, cli_runner):
        requests_mock.patch(
            self.queue_url,
            additional_matcher=partial(match_uploaded_json, {"name": self.name}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )
        result = cli_runner.invoke(change_command, [self.queue_id, "-n", self.name])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    @pytest.mark.usefixtures("create_queue_urls", "create_queue_schema")
    def test_schema(self, requests_mock, cli_runner):
        requests_mock.patch(
            self.queue_url,
            additional_matcher=partial(match_uploaded_json, {"schema": SCHEMA_URL}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )
        result = cli_runner.invoke(
            change_command, [self.queue_id, "--schema-content-file", SCHEMA_FILE_NAME]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output
