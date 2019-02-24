import pytest

from elisctl import __version__
from elisctl.lib.api_client import APIClient
from tests.conftest import API_URL


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": "some", "ELIS_PASSWORD": "secret"}
)
class TestAPIClient:
    api_client = APIClient()

    @pytest.mark.usefixtures("mock_login_request")
    def test_user_agent_header(self, requests_mock, isolated_cli_runner):
        requests_mock.get(
            API_URL + "/v1/", request_headers={"User-Agent": f"elisctl/{__version__}"}
        )
        with isolated_cli_runner.isolation():
            self.api_client.get("")
        assert requests_mock.called
