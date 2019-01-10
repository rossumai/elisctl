import pytest
from _pytest.fixtures import FixtureRequest

API_URL = "mock://api.elis.rossum.ai"
TOKEN = "secretsecret"


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
        f"{API_URL}/v1/schemas/{schema_id}",
        json={
            "content": schema_content,
            "name": "test",
            "queues": [f"{API_URL}/v1/queues/{i}" for i in range(1, 3)],
        },
        request_headers={"Authorization": f"Token {TOKEN}"},
    )
    yield requests_mock
