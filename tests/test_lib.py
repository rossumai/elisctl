import json

import click
import pytest

from elisctl import __version__
from elisctl.lib.api_client import APIClient
from tests.conftest import TOKEN, LOGIN_URL, API_URL


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": "some", "ELIS_PASSWORD": "secret"}
)
class TestAPIClient:
    api_client = APIClient()

    def test_get_token_success(self, requests_mock, isolated_cli_runner):
        requests_mock.post(LOGIN_URL, json={"key": TOKEN})
        with isolated_cli_runner.isolation():
            assert TOKEN == self.api_client.get_token()

    def test_get_token_failed(self, requests_mock, isolated_cli_runner):
        requests_mock.post(LOGIN_URL, status_code=401)
        with isolated_cli_runner.isolation(), pytest.raises(click.ClickException) as e:
            self.api_client.get_token()
        assert "Login failed with the provided credentials." == str(e.value)

    def test_get_token_error(self, requests_mock, isolated_cli_runner):
        error_json = {"password": ["required"]}
        requests_mock.post(LOGIN_URL, status_code=400, json=error_json)
        with isolated_cli_runner.isolation(), pytest.raises(click.ClickException) as e:
            self.api_client.get_token()
        assert f"Invalid response [{LOGIN_URL}]: {json.dumps(error_json)}" == str(e.value)

    @pytest.mark.usefixtures("mock_login_request")
    def test_user_agent_header(self, requests_mock, isolated_cli_runner):
        requests_mock.get(
            API_URL + "/v1/", request_headers={"User-Agent": f"elisctl/{__version__}"}
        )
        with isolated_cli_runner.isolation():
            self.api_client.get("")
        assert requests_mock.called
