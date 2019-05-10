import re
from functools import partial
from itertools import chain
from traceback import print_tb
from unittest import mock

import pytest

from elisctl.connector import list_command, change_command, delete_command, create_command
from tests.conftest import API_URL, TOKEN, match_uploaded_json, QUEUES_URL, CONNECTORS_URL

USERNAME = "test_user@rossum.ai"
PASSWORD = "secret"

QUEUES = ["1", "2"]
QUEUE_ID = "12345"
QUEUES_URLS = [f"{QUEUES_URL}/{id_}" for id_ in QUEUES]

CONNECTOR_ID = "101"
CONNECTOR_NAME = "My First Connector"
SERVICE_URL = "http://connector.somewhere.com:5000"
PARAMS = "strict=true"
AUTH_TOKEN = "secretly_secret"
ASYNCHRONOUS = True


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
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
            json={"id": CONNECTOR_ID, "name": CONNECTOR_NAME},
        )

        result = cli_runner.invoke(
            create_command,
            [CONNECTOR_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + ["-u", SERVICE_URL, "-p", PARAMS, "-a", ASYNCHRONOUS],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert f"{CONNECTOR_ID}, {CONNECTOR_NAME}\n" == result.output


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestList:
    def test_success(self, requests_mock, cli_runner):

        queue_url = f"{QUEUES_URL}/{QUEUE_ID}"

        requests_mock.get(
            f"{QUEUES_URL}",
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"url": f"{QUEUES_URL}/{QUEUE_ID}", "id": f"{QUEUE_ID}"}],
            },
        )

        requests_mock.get(
            CONNECTORS_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [
                    {
                        "id": CONNECTOR_ID,
                        "name": CONNECTOR_NAME,
                        "queues": [queue_url],
                        "service_url": SERVICE_URL,
                        "params": PARAMS,
                        "authorization_token": AUTH_TOKEN,
                        "asynchronous": ASYNCHRONOUS,
                    }
                ],
            },
        )

        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])

        expected_table = f"""\
  id  name                service url                            queues  params       asynchronous    authorization_token
----  ------------------  -----------------------------------  --------  -----------  --------------  ---------------------
 {CONNECTOR_ID}  {CONNECTOR_NAME}  {SERVICE_URL}     {QUEUE_ID}  {PARAMS}  {ASYNCHRONOUS}            {AUTH_TOKEN}
"""
        assert result.output == expected_table


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
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


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
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
