import json
import re
from traceback import print_tb

from click.testing import CliRunner
import requests_mock

from tools import download

DATA = """\
1;abc
2;cde
3;fgh\
"""
USERNAME = "something"
PASSWORD = "secret"


class TestDownload:
    def test_csv(self):
        url = "mock://csv.example.com"

        runner = CliRunner(
            env={"ADMIN_API_URL": url, "ADMIN_API_LOGIN": USERNAME, "ADMIN_API_PASSWORD": PASSWORD}
        )
        with requests_mock.mock() as m:
            m.get(re.compile(fr"{url}/byperiod/\d+/\d{{10}}"), text=DATA)
            result = runner.invoke(download.cli, ["csv", "--step", "1"])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert 1 == len(m.request_history)
        assert DATA == result.stdout.strip()

    def test_schema(self):
        url = "mock://api.elis.rossum.ai"
        schema_id = "1"
        schema_content = []

        runner = CliRunner(
            env={"ADMIN_API_URL": url, "ADMIN_API_LOGIN": USERNAME, "ADMIN_API_PASSWORD": PASSWORD}
        )
        with requests_mock.mock() as m:
            m.post(f"{url}/v1/auth/login", json={"key": "secretsecret"})
            m.post(f"{url}/v1/auth/logout")
            m.get(
                f"{url}/v1/schemas/{schema_id}",
                json={"content": schema_content},
                request_headers={"Authorization": "Token secretsecret"},
            )
            result = runner.invoke(download.cli, ["schema", schema_id])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert schema_content == json.loads(result.stdout)
