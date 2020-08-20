import json
from functools import partial
from traceback import print_tb

import pytest

from rossumctl.user_assignment import add_command, list_command, remove_command
from tests.conftest import QUEUES_URL, TOKEN, USERS_URL, match_uploaded_json


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
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


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestAdd:
    orig_queue_url = f"{QUEUES_URL}/1"
    new_queue_id = "2"
    new_queue_url = f"{QUEUES_URL}/{new_queue_id}"
    user_id = "3"
    user_url = f"{USERS_URL}/{user_id}"

    def test_success(self, requests_mock, cli_runner):
        requests_mock.get(self.user_url, json={"queues": [self.orig_queue_url]})
        requests_mock.get(self.new_queue_url, json={"url": self.new_queue_url})
        requests_mock.patch(
            self.user_url,
            additional_matcher=partial(
                match_uploaded_json, {"queues": [self.orig_queue_url, self.new_queue_url]}
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )
        result = cli_runner.invoke(add_command, ["-q", self.new_queue_id, "-u", self.user_id])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_queue_not_found(self, requests_mock, cli_runner):
        error = {"detail": "Not found."}
        requests_mock.get(self.user_url, json={"queues": [self.orig_queue_url]})
        requests_mock.get(self.new_queue_url, status_code=404, json=error)
        result = cli_runner.invoke(add_command, ["-q", self.new_queue_id, "-u", self.user_id])
        assert result.exit_code == 1, print_tb(result.exc_info[2])
        assert result.output == (
            f"Error: Invalid response [{self.new_queue_url}]: {json.dumps(error)}\n"
        )


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestRemoveQueues:
    orig_queue_id = "1"
    orig_queue_url = f"{QUEUES_URL}/{orig_queue_id}"
    removed_queue_id = "2"
    removed_queue_url = f"{QUEUES_URL}/{removed_queue_id}"
    user_id = "3"
    user_url = f"{USERS_URL}/{user_id}"

    def test_success(self, requests_mock, cli_runner):
        requests_mock.get(
            f"{QUEUES_URL}?users={self.user_id}",
            json={
                "pagination": {"total": 2, "next": None},
                "results": [
                    {"id": self.orig_queue_id, "url": self.orig_queue_url},
                    {"id": self.removed_queue_id, "url": self.removed_queue_url},
                ],
            },
            complete_qs=True,
        )
        requests_mock.patch(
            self.user_url,
            additional_matcher=partial(match_uploaded_json, {"queues": [self.orig_queue_url]}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )
        result = cli_runner.invoke(
            remove_command, ["-q", self.removed_queue_id, "-u", self.user_id]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output
