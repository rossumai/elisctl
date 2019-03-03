import json

import click
import pytest

from elisctl.lib.api_client import APIClient, ELISClient
from tests.conftest import API_URL, USERS_URL, ORGANIZATIONS_URL, TOKEN, LOGIN_URL, REQUEST_HEADERS


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
        requests_mock.get(API_URL + "/v1/", request_headers=REQUEST_HEADERS)
        with isolated_cli_runner.isolation():
            self.api_client.get("")
        assert requests_mock.called


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": "some", "ELIS_PASSWORD": "secret"}
)
class TestELISClient:
    api_client = ELISClient()

    @pytest.mark.usefixtures("mock_login_request")
    def test_get_organization_old_api(self, requests_mock, isolated_cli_runner):
        organization_json = {"test": "test"}

        user_url = f"{USERS_URL}/1"
        organization_url = f"{ORGANIZATIONS_URL}/1"
        requests_mock.get(f"{API_URL}/v1/auth/user", json={"url": user_url})
        requests_mock.get(user_url, json={"organization": organization_url})
        requests_mock.get(organization_url, json=organization_json)

        with isolated_cli_runner.isolation():
            assert organization_json == self.api_client.get_organization()
        assert requests_mock.called
