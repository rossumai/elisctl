from functools import partial
from itertools import chain
from traceback import print_tb
from typing import Optional

import pytest

from elisctl.queue import create_command, list_command, delete_command, change_command
from tests.conftest import (
    TOKEN,
    match_uploaded_json,
    WORKSPACES_URL,
    SCHEMAS_URL,
    QUEUES_URL,
    INBOXES_URL,
    USERS_URL,
    CONNECTORS_URL,
    WEBHOOKS_URL,
)

WORKSPACE_ID = "1"
WORKSPACE_URL = f"{WORKSPACES_URL}/{WORKSPACE_ID}"
SCHEMA_URL = f"{SCHEMAS_URL}/1"
SCHEMA_FILE_NAME = "schema.json"


class QueueFixtures:
    name: Optional[str] = None
    queue_id: Optional[str] = None
    inbox_url: Optional[str] = None

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

        create_queue_content = {
            "name": self.name,
            "workspace": WORKSPACE_URL,
            "schema": SCHEMA_URL,
            "rir_url": "https://all.rir.rossum.ai",
            "webhooks": [],
        }
        requests_mock.post(
            QUEUES_URL,
            additional_matcher=partial(match_uploaded_json, create_queue_content),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": self.queue_id,
                "url": self.queue_url,
                "inbox": self.inbox_url,
                "name": self.name,
            },
        )

        queue_content_incl_inbox = {
            **create_queue_content,
            "inbox": self.inbox_url,
            "url": self.queue_url,
        }

        requests_mock.get(
            self.queue_url,
            json=queue_content_incl_inbox,
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

    @pytest.fixture
    def create_queue_schema(self, isolated_cli_runner):
        with open(SCHEMA_FILE_NAME, "w") as schema:
            print("[]", file=schema)

    @property
    def queue_url(self) -> str:
        return f"{QUEUES_URL}/{self.queue_id}"


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
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
        email = f"{email_prefix}-aaaaaa@elis.localhost"

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
                    "email_prefix": email_prefix,
                    "bounce_email_to": bounce_mail,
                    "bounce_unprocessable_attachments": True,
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"email": email},
        )

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

    @pytest.mark.usefixtures("create_queue_urls", "create_queue_schema")
    def test_create_queue_with_webhooks(self, requests_mock, isolated_cli_runner):
        first_webhook_id = 101
        second_webhook_id = 202
        webhooks = [first_webhook_id, second_webhook_id]

        requests_mock.get(
            f"{WEBHOOKS_URL}/{first_webhook_id}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": first_webhook_id, "url": f"{WEBHOOKS_URL}/{first_webhook_id}"},
        )

        requests_mock.get(
            f"{WEBHOOKS_URL}/{second_webhook_id}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": second_webhook_id, "url": f"{WEBHOOKS_URL}/{second_webhook_id}"},
        )

        queue_content = {
            "name": self.name,
            "workspace": WORKSPACE_URL,
            "schema": SCHEMA_URL,
            "rir_url": "https://all.rir.rossum.ai",
            "webhooks": [f"{WEBHOOKS_URL}/{id_}" for id_ in webhooks],
        }

        requests_mock.post(
            QUEUES_URL,
            additional_matcher=partial(match_uploaded_json, queue_content),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": self.queue_id, "url": self.queue_url},
        )

        result = isolated_cli_runner.invoke(
            create_command,
            [self.name, "--schema-content-file", SCHEMA_FILE_NAME]
            + list(chain.from_iterable(("--webhook-id", w) for w in webhooks)),
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{self.queue_id}, no email-prefix specified\n" == result.output


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
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
        webhook_ids = ["101", "202"]
        webhooks_urls = [f"{WEBHOOKS_URL}/{id_}" for id_ in webhook_ids]

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
                        "webhooks": webhooks_urls,
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
        requests_mock.get(
            WEBHOOKS_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [
                    {"id": id_, "url": webhook} for id_, webhook in zip(webhook_ids, webhooks_urls)
                ],
            },
        )

        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  name         workspace  inbox               schema  users    connector                                         webhooks
----  ---------  -----------  ----------------  --------  -------  ------------------------------------------------  ----------
   {queue_id}  {name}            {workspace_id}  {inbox}         {schema_id}  {', '.join(user_ids)}     {connector_url}  {', '.join(webhook_ids)}
"""
        assert result.output == expected_table


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
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


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestChange(QueueFixtures):
    name = "TestName"
    queue_id = "1"
    first_webhook_id = 101
    second_webhook_id = 202
    webhooks = [first_webhook_id, second_webhook_id]
    webhook_urls = [f"{WEBHOOKS_URL}/{id_}" for id_ in webhooks]
    inbox_id = "1"
    email_prefix = "test-email-prefix"
    inbox_email = f"{email_prefix}-aaaaaa@elis.rossum.ai"

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

    @pytest.mark.usefixtures("create_queue_urls")
    def test_create_inbox_on_queue_change(self, requests_mock, isolated_cli_runner):
        bounce_mail = "test@example.com"
        name = "My First Queue"

        requests_mock.get(
            f"{QUEUES_URL}/{self.queue_id}",
            json={"name": name, "inbox": None, "url": f"{QUEUES_URL}/{self.queue_id}"},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            INBOXES_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": f"{name} inbox",
                    "email_prefix": self.email_prefix,
                    "bounce_email_to": bounce_mail,
                    "bounce_unprocessable_attachments": True,
                    "queues": [f"{QUEUES_URL}/{self.queue_id}"],
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": self.inbox_id, "email": self.inbox_email, "bounce_email_to": bounce_mail},
        )

        result = isolated_cli_runner.invoke(
            change_command,
            [self.queue_id, "--email-prefix", self.email_prefix, "--bounce-email", bounce_mail],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == f"{self.inbox_id}, {self.inbox_email}, test@example.com\n"

    def test_update_inbox_on_queue_change(self, requests_mock, isolated_cli_runner):
        bounce_mail = "test@example.com"

        requests_mock.get(
            f"{QUEUES_URL}/{self.queue_id}",
            json={"inbox": f"{INBOXES_URL}/{self.inbox_id}"},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.patch(
            f"{INBOXES_URL}/{self.inbox_id}",
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "email_prefix": self.email_prefix,
                    "bounce_email_to": bounce_mail,
                    "bounce_unprocessable_attachments": True,
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
            json={"id": self.inbox_id, "email": self.inbox_email, "bounce_email_to": bounce_mail},
        )

        requests_mock.patch(
            self.queue_url,
            additional_matcher=partial(match_uploaded_json, {}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )

        result = isolated_cli_runner.invoke(
            change_command,
            [self.queue_id, "--email-prefix", self.email_prefix, "--bounce-email", bounce_mail],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == f"{self.inbox_id}, {self.inbox_email}, {bounce_mail}\n"

    @pytest.mark.usefixtures("create_queue_urls")
    def test_cannot_create_inbox_on_queue_change(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            change_command, [self.queue_id, "--email-prefix", self.email_prefix]
        )
        assert result.exit_code == 1, print_tb(result.exc_info[2])
        assert (
            "Error: Inbox cannot be created without both bounce email and email prefix specified.\n"
            == result.output
        )

    def test_change_webhook_ids(self, requests_mock, cli_runner):
        requests_mock.get(
            f"{WEBHOOKS_URL}/{self.first_webhook_id}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": self.first_webhook_id, "url": f"{WEBHOOKS_URL}/{self.first_webhook_id}"},
        )

        requests_mock.get(
            f"{WEBHOOKS_URL}/{self.second_webhook_id}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": self.second_webhook_id, "url": f"{WEBHOOKS_URL}/{self.second_webhook_id}"},
        )

        requests_mock.patch(
            self.queue_url,
            additional_matcher=partial(
                match_uploaded_json, {"name": self.name, "webhooks": self.webhook_urls}
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )
        result = cli_runner.invoke(
            change_command,
            [self.queue_id, "-n", self.name]
            + list(chain.from_iterable(("--webhook-id", w) for w in self.webhooks)),
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output
