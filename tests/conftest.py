import email
import json
import os
import re
from platform import platform
from typing import Dict, Tuple

import pytest
from _pytest.fixtures import FixtureRequest
from requests_mock.request import _RequestObjectProxy as Request

from elisctl import __version__

API_URL = "httpmock://api.elis.rossum.ai"
TOKEN = "secretsecret"

ORGANIZATIONS_URL = f"{API_URL}/v1/organizations"
WORKSPACES_URL = f"{API_URL}/v1/workspaces"
DOCUMENTS_URL = f"{API_URL}/v1/documents"
ANNOTATIONS_URL = f"{API_URL}/v1/annotations"
PAGES_URL = f"{API_URL}/v1/pages"
QUEUES_URL = f"{API_URL}/v1/queues"
INBOXES_URL = f"{API_URL}/v1/inboxes"
SCHEMAS_URL = f"{API_URL}/v1/schemas"
USERS_URL = f"{API_URL}/v1/users"
GROUPS_URL = f"{API_URL}/v1/groups"
LOGIN_URL = f"{API_URL}/v1/auth/login"
CONNECTORS_URL = f"{API_URL}/v1/connectors"
HOOKS_URL = f"{API_URL}/v1/hooks"

REQUEST_HEADERS = {"User-Agent": f"elisctl/{__version__} ({platform()})"}


@pytest.fixture
def elis_credentials(monkeypatch):
    monkeypatch.setitem(os.environ, "ELIS_URL", API_URL)
    monkeypatch.setitem(os.environ, "ELIS_USERNAME", "some")
    monkeypatch.setitem(os.environ, "ELIS_PASSWORD", "secret")


@pytest.fixture
def mock_login_request(requests_mock):
    requests_mock.post(LOGIN_URL, json={"key": TOKEN}, request_headers=REQUEST_HEADERS)
    requests_mock.post(f"{API_URL}/v1/auth/logout", request_headers=REQUEST_HEADERS)
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

    requests_mock.get(
        f"{API_URL}/v1/auth/user", json={"url": user_url, "organization": organization_url}
    )

    requests_mock.get(
        re.compile(fr"{WORKSPACES_URL}/\d$"),
        json={"organization": organization_url},
        request_headers={"Authorization": f"Token {TOKEN}"},
    )


@pytest.fixture
def mock_file(tmp_path):
    invoice_sample = tmp_path / "empty_file.pdf"
    invoice_sample.write_bytes(_EMPTY_PDF_FILE)
    yield invoice_sample


def match_uploaded_json(uploaded_json: dict, request: Request) -> bool:
    return request.json() == uploaded_json


def match_uploaded_data(filename: str, request: Request) -> bool:
    return filename in request.text


def match_uploaded_values(values: dict, request: Request) -> bool:
    return values == json.loads(parse_multipart_message(request)["values"][1])


def parse_multipart_message(request: Request) -> Dict[str, Tuple[Dict[str, str], str]]:
    epost_data = f"""\
MIME-Version: 1.0
Content-Type: {request.headers['Content-Type']}

{request.body.decode()}"""

    msg = email.message_from_string(epost_data)

    assert msg.is_multipart()

    return {
        params["name"]: (params, contents)
        for params, contents in map(
            lambda part: (dict(part.get_params(header="content-disposition")), part.get_payload()),
            msg.get_payload(),
        )
    }


_EMPTY_PDF_FILE = b"""%PDF-1.3
1 0 obj
<<
/Type /Pages
/Count 1
/Kids [ 3 0 R ]
>>
endobj
2 0 obj
<<
/Producer (PyPDF2)
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 1 0 R
/Resources <<
>>
/MediaBox [ 0 0 10 10 ]
>>
endobj
4 0 obj
<<
/Type /Catalog
/Pages 1 0 R
>>
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000068 00000 n
0000000108 00000 n
0000000196 00000 n
trailer
<<
/Size 5
/Root 4 0 R
/Info 2 0 R
>>
startxref
245
%%EOF
"""

_EMPTY_PNG_FILE = b"""\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x03\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03PLTE\x00\x00\x00\xa7z=\xda\x00\x00\x00\x01tRNS\x00@\xe6\xd8f\x00\x00\x00\nIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"""
