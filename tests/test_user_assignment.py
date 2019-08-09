from traceback import print_tb

import pytest

from elisctl.user_assignment import list_command
from tests.conftest import USERS_URL, QUEUES_URL, API_URL

USERNAME = "test_user@rossum.ai"
PASSWORD = "secret"


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestList:
    queue_ids = ["1", "2"]
    name = "TestQueue"
    user_ids = ["5", "4"]
    user_urls = [f"{USERS_URL}/{id_}" for id_ in user_ids]
    queue_urls = [f"{QUEUES_URL}/{id_}" for id_ in queue_ids]

    @pytest.fixture
    def urls(self, requests_mock):
        requests_mock.get(
            f"{QUEUES_URL}",
            json={
                "pagination": {"total": 2, "next": None},
                "results": [
                    {"id": id_, "url": url, "name": self.name, "users": self.user_urls}
                    for id_, url in zip(self.queue_ids, self.queue_urls)
                ],
            },
        )

        requests_mock.get(
            USERS_URL,
            json={
                "pagination": {"total": 2, "next": None},
                "results": [
                    {"id": id_, "url": url, "username": f"user_{id_}"}
                    for id_, url in zip(self.user_ids, self.user_urls)
                ],
            },
        )

    @pytest.mark.usefixtures("urls")
    def test_no_filter(self, cli_runner):
        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  username      queue id  queue name
----  ----------  ----------  ------------
   {self.user_ids[1]}  user_{self.user_ids[1]}               {self.queue_ids[0]}  {self.name}
                           {self.queue_ids[1]}  {self.name}
   {self.user_ids[0]}  user_{self.user_ids[0]}               {self.queue_ids[0]}  {self.name}
                           {self.queue_ids[1]}  {self.name}
"""
        assert result.output == expected_table

    @pytest.mark.usefixtures("urls")
    def test_queue_filter(self, cli_runner):
        result = cli_runner.invoke(list_command, ["-q", self.queue_ids[0]])
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  username      queue id  queue name
----  ----------  ----------  ------------
   {self.user_ids[1]}  user_{self.user_ids[1]}               {self.queue_ids[0]}  {self.name}
   {self.user_ids[0]}  user_{self.user_ids[0]}               {self.queue_ids[0]}  {self.name}
"""
        assert result.output == expected_table

    @pytest.mark.usefixtures("urls")
    def test_user_filter(self, cli_runner):
        result = cli_runner.invoke(list_command, ["-u", self.user_ids[0]])
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  username      queue id  queue name
----  ----------  ----------  ------------
   {self.user_ids[0]}  user_{self.user_ids[0]}               {self.queue_ids[0]}  {self.name}
                           {self.queue_ids[1]}  {self.name}
"""
        assert result.output == expected_table

    @pytest.mark.usefixtures("urls")
    def test_queue_user_filter(self, cli_runner):
        result = cli_runner.invoke(list_command, ["-u", self.user_ids[0], "-q", self.queue_ids[0]])
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  username      queue id  queue name
----  ----------  ----------  ------------
   {self.user_ids[0]}  user_{self.user_ids[0]}               {self.queue_ids[0]}  {self.name}
"""
        assert result.output == expected_table
