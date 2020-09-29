import re
from functools import partial
from itertools import chain
from traceback import print_tb, format_tb

import pytest

from elisctl.hook import list_command, change_command, delete_command, create_command
from tests.conftest import TOKEN, match_uploaded_json, QUEUES_URL, HOOKS_URL

QUEUES = ["1", "2"]
QUEUE_ID = "12345"
QUEUES_URLS = [f"{QUEUES_URL}/{id_}" for id_ in QUEUES]
DEFAULT_QUEUE_URL = f"{QUEUES_URL}/{QUEUE_ID}"

HOOK_ID = "101"
HOOK_NAME = "My First Hook"
EVENTS = ["annotation_status", "another_event"]
CONFIG_URL = "http://hook.somewhere.com:5000"
CONFIG_SECRET = "some_secret_key"
ACTIVE = True


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestCreate:
    def test_success(self, requests_mock, cli_runner):

        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + ["--active", ACTIVE, "--config-url", CONFIG_URL, "--config-secret", CONFIG_SECRET],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}, {CONFIG_URL}\n"
        )

    def test_missing_queue_id(self, requests_mock, cli_runner):

        requests_mock.get(
            QUEUES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": QUEUE_ID, "url": DEFAULT_QUEUE_URL}],
            },
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "queues": [DEFAULT_QUEUE_URL],
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"url": CONFIG_URL, "secret": None, "insecure_ssl": False},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                "events": EVENTS,
                "config": {"url": CONFIG_URL},
            },
        )

        requests_mock.get(
            HOOKS_URL,
            json={"results": [{"id": HOOK_ID, "name": HOOK_NAME, "queues": [DEFAULT_QUEUE_URL]}]},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + ["--active", ACTIVE, "--config-url", CONFIG_URL],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert (
            f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}, {CONFIG_URL}\n"
            == result.output
        )


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestList:
    def test_success(self, requests_mock, cli_runner):
        result = self._test_list(cli_runner, requests_mock, True)

        expected_table = f"""\
  id  name           events                              queues  active    url                             insecure_ssl    secret
----  -------------  --------------------------------  --------  --------  ------------------------------  --------------  ---------------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      {CONFIG_URL}  False           {CONFIG_SECRET}
"""
        assert result.output == expected_table

    def test_non_admin_does_not_see_auth_token(self, requests_mock, cli_runner):
        result = self._test_list(cli_runner, requests_mock, False)

        expected_table = f"""\
  id  name           events                              queues  active    url                             insecure_ssl
----  -------------  --------------------------------  --------  --------  ------------------------------  --------------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      {CONFIG_URL}  False
"""
        assert result.output == expected_table

    @staticmethod
    def _test_list(cli_runner, requests_mock, include_secret: bool):
        queue_url = f"{QUEUES_URL}/{QUEUE_ID}"
        requests_mock.get(
            f"{QUEUES_URL}",
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"url": queue_url, "id": QUEUE_ID}],
            },
        )

        hook_result = {
            "id": HOOK_ID,
            "name": HOOK_NAME,
            "queues": [queue_url],
            "active": ACTIVE,
            "events": EVENTS,
            "config": {"url": CONFIG_URL, "insecure_ssl": False},
        }

        if include_secret:
            hook_result["config"].update({"secret": CONFIG_SECRET})  # type: ignore

        requests_mock.get(
            HOOKS_URL, json={"pagination": {"total": 1, "next": None}, "results": [hook_result]}
        )
        result = cli_runner.invoke(list_command)
        assert not result.exit_code, format_tb(result.exc_info[2])
        return result


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestChange:
    new_hook_name = "My patched new name"
    new_event = "new_event"

    def test_success(self, requests_mock, cli_runner):

        requests_mock.get(f"{QUEUES_URL}/{QUEUE_ID}", json={"url": f"{QUEUES_URL}/{QUEUE_ID}"})

        requests_mock.patch(
            f"{HOOKS_URL}/{HOOK_ID}",
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                    "name": self.new_hook_name,
                    "events": [self.new_event],
                    "active": True,
                    "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )

        result = cli_runner.invoke(
            change_command,
            [
                HOOK_ID,
                "-q",
                QUEUE_ID,
                "-n",
                self.new_hook_name,
                "-e",
                self.new_event,
                "--config-url",
                CONFIG_URL,
                "--config-secret",
                CONFIG_SECRET,
            ],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_noop(self, requests_mock, cli_runner):
        cli_runner.invoke(change_command, [HOOK_ID])
        assert not requests_mock.called


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestDelete:
    def test_success(self, requests_mock, cli_runner):

        requests_mock.get(
            f"{HOOKS_URL}/{HOOK_ID}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": HOOK_ID, "url": HOOKS_URL},
        )

        requests_mock.delete(
            f"{HOOKS_URL}/{HOOK_ID}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=204,
        )

        result = cli_runner.invoke(delete_command, [HOOK_ID, "--yes"])
        assert not result.exit_code, print_tb(result.exc_info[2])
