import json
from functools import partial

import click
import pytest

from elisctl.lib import APIObject, ANNOTATIONS
from elisctl.lib.api_client import APIClient, ELISClient
from tests.conftest import (
    ANNOTATIONS_URL,
    API_URL,
    SCHEMAS_URL,
    USERS_URL,
    ORGANIZATIONS_URL,
    PAGES_URL,
    TOKEN,
    LOGIN_URL,
    REQUEST_HEADERS,
    DOCUMENTS_URL,
    QUEUES_URL,
    match_uploaded_data,
    match_uploaded_json,
    match_uploaded_values,
)

UPLOADED_DOC = f"{DOCUMENTS_URL}/12345"
SCHEMA_ID = 398431
SCHEMA_URL = f"{SCHEMAS_URL}/{SCHEMA_ID}"
QUEUE_ID = 20202
QUEUE_URL = f"{QUEUES_URL}/{QUEUE_ID}"
UPLOAD_ENDPOINT = f"{QUEUE_URL}/upload"
DOCUMENT_ID = 315511
DOCUMENT_URL = f"{DOCUMENTS_URL}/{DOCUMENT_ID}"
PAGE_ID = 4210254
PAGE_URL = f"{PAGES_URL}/{PAGE_ID}"
ANNOTATION_ID = 1863864
ANNOTATION_URL = f"{ANNOTATIONS_URL}/{ANNOTATION_ID}"


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": "some", "ELIS_PASSWORD": "secret"}
)
class TestAPIClient:
    api_client = APIClient(None)

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
@pytest.mark.usefixtures("mock_login_request")
class TestSideload:
    api_client = APIClient(None)
    url = f"{API_URL}/v1/tests"
    obj_url = f"{url}/1"
    sideloaded_obj = {"url": obj_url, "some": "test"}
    TESTS = APIObject("tests")

    def test_sideload_singular(self, requests_mock, isolated_cli_runner):
        requests_mock.get(self.url, json=self._paginated_rsp())

        with isolated_cli_runner.isolation():
            res = self.api_client._sideload([{"test": self.obj_url}], (self.TESTS,))
        assert res == [{"test": self.sideloaded_obj}]

    def test_sideload_plural(self, requests_mock, isolated_cli_runner):
        requests_mock.get(self.url, json=self._paginated_rsp())

        with isolated_cli_runner.isolation():
            res = self.api_client._sideload([{"tests": [self.obj_url]}], (self.TESTS,))
        assert res == [{"tests": [self.sideloaded_obj]}]

    def test_sideload_not_reachable_singular(self, requests_mock, isolated_cli_runner):
        requests_mock.get(self.url, json=self._paginated_rsp(0))

        with isolated_cli_runner.isolation():
            res = self.api_client._sideload([{"test": self.obj_url}], (self.TESTS,))
        assert res == [{"test": {}}]

    def test_sideload_not_reachable_plural(self, requests_mock, isolated_cli_runner):
        requests_mock.get(self.url, json=self._paginated_rsp(0))

        with isolated_cli_runner.isolation():
            res = self.api_client._sideload([{"tests": [self.obj_url]}], (self.TESTS,))
        assert res == [{"tests": []}]

    def _paginated_rsp(self, total: int = 1):
        assert total <= 1, "URL in sideloaded_obj is not unique."
        return {
            "results": [self.sideloaded_obj for _ in range(total)],
            "pagination": {"next": None, "total": total},
        }


@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": "some", "ELIS_PASSWORD": "secret"}
)
class TestELISClient:
    api_client = ELISClient(None)

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

    @pytest.mark.usefixtures("mock_login_request")
    def test_upload_overwrite_filename(self, requests_mock, isolated_cli_runner, mock_file):
        original_filename = "empty_file.pdf"
        overwritten_filename = "Overwritten filename.pdf"
        api_response = {"results": [{"document": DOCUMENT_URL}]}

        requests_mock.post(
            UPLOAD_ENDPOINT,
            additional_matcher=partial(match_uploaded_data, original_filename),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"results": [{"document": DOCUMENT_URL}]},
            status_code=201,
        )

        with isolated_cli_runner.isolation():
            assert api_response == self.api_client.upload_document(QUEUE_ID, mock_file)

        requests_mock.post(
            UPLOAD_ENDPOINT,
            additional_matcher=partial(match_uploaded_data, overwritten_filename),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"results": [{"document": DOCUMENT_URL}]},
            status_code=201,
        )

        with isolated_cli_runner.isolation():
            assert api_response == self.api_client.upload_document(
                QUEUE_ID, mock_file, overwritten_filename
            )

    @pytest.mark.usefixtures("mock_login_request")
    def test_upload_values(self, requests_mock, isolated_cli_runner, mock_file):
        values = {"upload:key_1": "value_1", "upload:key_2": "value_2"}
        api_response = {
            "document": DOCUMENT_URL,
            "annotation": ANNOTATION_URL,
            "results": [{"document": DOCUMENT_URL, "annotation": ANNOTATION_URL}],
        }

        requests_mock.post(
            UPLOAD_ENDPOINT,
            additional_matcher=partial(match_uploaded_values, values),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json=api_response,
            status_code=201,
        )

        with isolated_cli_runner.isolation():
            assert api_response == self.api_client.upload_document(
                QUEUE_ID, mock_file, values=values
            )

    @pytest.mark.usefixtures("mock_login_request")
    def test_set_metadata(self, requests_mock, isolated_cli_runner):
        metadata = {"key_1": 42, "key_2": "str_value", "nested_key": {"key_a": "value_a"}}
        api_response = {
            "document": DOCUMENT_URL,
            "id": DOCUMENT_ID,
            "queue": QUEUE_URL,
            "schema": SCHEMA_URL,
            "pages": [PAGE_URL],
            "modifier": None,
            "modified_at": None,
            "confirmed_at": None,
            "exported_at": None,
            "assigned_at": None,
            "status": "to_review",
            "rir_poll_id": "de8fb2e5877741bf97808eda",
            "messages": None,
            "url": ANNOTATION_URL,
            "content": f"{ANNOTATION_URL}/content",
            "time_spent": 0.0,
            "metadata": metadata,
        }

        requests_mock.patch(
            ANNOTATION_URL,
            additional_matcher=partial(match_uploaded_json, {"metadata": metadata}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json=api_response,
            status_code=200,
        )

        with isolated_cli_runner.isolation():
            assert api_response == self.api_client.set_metadata(
                ANNOTATIONS, ANNOTATION_ID, metadata
            )
