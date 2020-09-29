import re
from functools import partial
from itertools import chain
from traceback import print_tb, format_tb
from unittest import mock

import pytest

from elisctl.connector import list_command, change_command, delete_command, create_command
from tests.conftest import TOKEN, match_uploaded_json, QUEUES_URL, CONNECTORS_URL

QUEUES = ["1", "2"]
QUEUE_ID = "12345"
QUEUES_URLS = [f"{QUEUES_URL}/{id_}" for id_ in QUEUES]
DEFAULT_QUEUE_URL = f"{QUEUES_URL}/{QUEUE_ID}"

CONNECTOR_ID = "101"
CONNECTOR_NAME = "My First Connector"
SERVICE_URL = "http://connector.somewhere.com:5000"
PARAMS = "strict=true"
AUTH_TOKEN = "secretly_secret"
ASYNCHRONOUS = True


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestCreate:
    @mock.patch("elisctl.connector._generate_token")
    def test_success(self, mock_token, requests_mock, cli_runner):
        mock_token.return_value = generated_token = TOKEN * 3

        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            CONNECTORS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": CONNECTOR_NAME,
                    "queues": QUEUES_URLS,
                    "service_url": SERVICE_URL,
                    "authorization_token": generated_token,
                    "params": PARAMS,
                    "asynchronous": ASYNCHRONOUS,
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={"id": CONNECTOR_ID, "name": CONNECTOR_NAME, "queues": [DEFAULT_QUEUE_URL]},
        )

        result = cli_runner.invoke(
            create_command,
            [CONNECTOR_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + ["-u", SERVICE_URL, "-p", PARAMS, "-a", ASYNCHRONOUS],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{CONNECTOR_ID}, {CONNECTOR_NAME}, ['{DEFAULT_QUEUE_URL}']\n" == result.output

    @mock.patch("elisctl.connector._generate_token")
    def test_missing_queue_id(self, mock_token, requests_mock, cli_runner):
        mock_token.return_value = generated_token = TOKEN * 3

        requests_mock.get(
            QUEUES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": QUEUE_ID, "url": DEFAULT_QUEUE_URL}],
            },
        )

        requests_mock.post(
            CONNECTORS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": CONNECTOR_NAME,
                    "queues": [DEFAULT_QUEUE_URL],
                    "service_url": SERVICE_URL,
                    "authorization_token": generated_token,
                    "params": PARAMS,
                    "asynchronous": ASYNCHRONOUS,
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": CONNECTOR_ID,
                "name": CONNECTOR_NAME,
                "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
            },
        )

        requests_mock.get(
            CONNECTORS_URL,
            json={
                "results": [
                    {
                        "id": "101",
                        "name": "My First Connector",
                        "queues": ["httpmock://api.elis.rossum.ai/v1/queues/12345"],
                    }
                ]
            },
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        result = cli_runner.invoke(
            create_command, [CONNECTOR_NAME, "-u", SERVICE_URL, "-p", PARAMS, "-a", ASYNCHRONOUS]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{CONNECTOR_ID}, {CONNECTOR_NAME}, ['{DEFAULT_QUEUE_URL}']\n" == result.output


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestList:
    def test_success(self, requests_mock, cli_runner):
        result = self._test_list(cli_runner, requests_mock, True)

        expected_table = f"""\
  id  name                service url                            queues  params       asynchronous    authorization_token
----  ------------------  -----------------------------------  --------  -----------  --------------  ---------------------
 {CONNECTOR_ID}  {CONNECTOR_NAME}  {SERVICE_URL}     {QUEUE_ID}  {PARAMS}  {ASYNCHRONOUS}            {AUTH_TOKEN}
"""
        assert result.output == expected_table

    def test_non_admin_does_not_see_auth_token(self, requests_mock, cli_runner):

        result = self._test_list(cli_runner, requests_mock, False)

        expected_table = f"""\
  id  name                service url                            queues  params       asynchronous
----  ------------------  -----------------------------------  --------  -----------  --------------
 {CONNECTOR_ID}  {CONNECTOR_NAME}  {SERVICE_URL}     {QUEUE_ID}  {PARAMS}  {ASYNCHRONOUS}
"""
        assert result.output == expected_table

    @staticmethod
    def _test_list(cli_runner, requests_mock, include_token: bool):
        queue_url = f"{QUEUES_URL}/{QUEUE_ID}"
        requests_mock.get(
            f"{QUEUES_URL}",
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"url": queue_url, "id": QUEUE_ID}],
            },
        )

        connector_result = {
            "id": CONNECTOR_ID,
            "name": CONNECTOR_NAME,
            "queues": [queue_url],
            "service_url": SERVICE_URL,
            "params": PARAMS,
            "asynchronous": ASYNCHRONOUS,
        }

        if include_token:
            connector_result["authorization_token"] = AUTH_TOKEN

        requests_mock.get(
            CONNECTORS_URL,
            json={"pagination": {"total": 1, "next": None}, "results": [connector_result]},
        )
        result = cli_runner.invoke(list_command)
        assert not result.exit_code, format_tb(result.exc_info[2])
        return result


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestChange:
    def test_success(self, requests_mock, cli_runner):

        requests_mock.get(f"{QUEUES_URL}/{QUEUE_ID}", json={"url": f"{QUEUES_URL}/{QUEUE_ID}"})

        requests_mock.patch(
            f"{CONNECTORS_URL}/{CONNECTOR_ID}",
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                    "authorization_token": AUTH_TOKEN,
                    "service_url": SERVICE_URL,
                    "asynchronous": True,
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )

        result = cli_runner.invoke(
            change_command, [CONNECTOR_ID, "-q", QUEUE_ID, "-t", AUTH_TOKEN, "-u", SERVICE_URL]
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_noop(self, requests_mock, cli_runner):
        cli_runner.invoke(change_command, [CONNECTOR_ID])
        assert not requests_mock.called


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestDelete:
    def test_success(self, requests_mock, cli_runner):

        requests_mock.get(
            f"{CONNECTORS_URL}/{CONNECTOR_ID}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": CONNECTOR_ID, "url": CONNECTORS_URL},
        )

        requests_mock.delete(
            f"{CONNECTORS_URL}/{CONNECTOR_ID}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=204,
        )

        result = cli_runner.invoke(delete_command, [CONNECTOR_ID, "--yes"])
        assert not result.exit_code, print_tb(result.exc_info[2])
