import re

import pytest
from _pytest.fixtures import FixtureRequest
from requests import Request

API_URL = "httpmock://api.elis.rossum.ai"
TOKEN = "secretsecret"

ORGANIZATIONS_URL = f"{API_URL}/v1/organizations"
WORKSPACES_URL = f"{API_URL}/v1/workspaces"
DOCUMENTS_URL = f"{API_URL}/v1/documents"
ANNOTATIONS_URL = f"{API_URL}/v1/annotations"
QUEUES_URL = f"{API_URL}/v1/queues"
INBOXES_URL = f"{API_URL}/v1/inboxes"
SCHEMAS_URL = f"{API_URL}/v1/schemas"
USERS_URL = f"{API_URL}/v1/users"
GROUPS_URL = f"{API_URL}/v1/groups"


@pytest.fixture
def mock_login_request(requests_mock):
    requests_mock.post(f"{API_URL}/v1/auth/login", json={"key": TOKEN})
    requests_mock.post(f"{API_URL}/v1/auth/logout")
    yield requests_mock


@pytest.fixture
def mock_get_schema(request: FixtureRequest, requests_mock):
    schema_id = getattr(request.module, "schema_id", "1")
    schema_content = getattr(request.module, "schema_content", [])

    requests_mock.get(
        f"{SCHEMAS_URL}/{schema_id}",
        json={
            "content": schema_content,
            "name": "test",
            "queues": [f"{API_URL}/v1/queues/{i}" for i in range(1, 3)],
        },
        request_headers={"Authorization": f"Token {TOKEN}"},
    )
    yield requests_mock


@pytest.fixture
def mock_organization_urls(request: FixtureRequest, requests_mock):
    organization_id = getattr(request.module, "ORGANIZATION_ID", "1")
    organization_url = getattr(
        request.module, "ORGANIZATION_URL", f"{ORGANIZATIONS_URL}/{organization_id}"
    )
    user_url = f"{USERS_URL}/1"

    requests_mock.get(
        organization_url,
        json={"url": organization_url, "id": organization_id},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )

    requests_mock.get(f"{API_URL}/v1/auth/user", json={"url": user_url})
    requests_mock.get(user_url, json={"organization": organization_url})

    requests_mock.get(
        re.compile(fr"{WORKSPACES_URL}/\d$"),
        json={"organization": organization_url},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )


def match_uploaded_json(uploaded_json: dict, request: Request) -> bool:
    return request.json() == uploaded_json
