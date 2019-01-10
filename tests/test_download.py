import json
import re
from traceback import print_tb

from click.testing import CliRunner

from tests.conftest import API_URL
from tools import download

DATA = """\
1;abc
2;cde
3;fgh\
"""
USERNAME = "something"
PASSWORD = "secret"


class TestDownload:
    def test_csv(self, requests_mock):
        url = "mock://csv.example.com"

        runner = CliRunner(
            env={"ADMIN_API_URL": url, "ADMIN_API_LOGIN": USERNAME, "ADMIN_API_PASSWORD": PASSWORD}
        )
        requests_mock.get(re.compile(fr"{url}/byperiod/\d+/\d{{10}}"), text=DATA)
        result = runner.invoke(download.cli, ["csv", "--step", "1"])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert 1 == len(requests_mock.request_history)
        assert DATA == result.stdout.strip()

    def test_schema(self, mock_login_request, mock_get_schema):
        schema_id = "1"
        schema_content = []

        runner = CliRunner(
            env={
                "ADMIN_API_URL": API_URL,
                "ADMIN_API_LOGIN": USERNAME,
                "ADMIN_API_PASSWORD": PASSWORD,
            }
        )
        result = runner.invoke(download.cli, ["schema", schema_id])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert schema_content == json.loads(result.stdout)
