import re
from traceback import print_tb
from unittest import mock

import pytest

from elisctl.document.extract_data import get_data
from tests.conftest import API_URL, TOKEN, QUEUES_URL, ANNOTATIONS_URL

USERNAME = "something"
PASSWORD = "secret"

ANNOTATION_IDS = [315510, 315511]
EXPORT_IDS_CHAIN = ",".join(str(id_) for id_ in ANNOTATION_IDS)

QUEUE_ID = "20202"
ANNOTATION_TO_REVIEW_ID = "315510"
ANNOTATION_FAILED_ID = "315511"
ANNOTATION_TO_REVIEW = f"{ANNOTATIONS_URL}/{ANNOTATION_TO_REVIEW_ID}"
ANNOTATION_FAILED = f"{ANNOTATIONS_URL}/{ANNOTATION_FAILED_ID}"

UPLOAD_ENDPOINT = f"{QUEUES_URL}/{QUEUE_ID}/upload"
EXPORT_ENDPOINT = f"{QUEUES_URL}/{QUEUE_ID}/export?id={EXPORT_IDS_CHAIN}&format=json"

OUTPUT_JSON = {"results": [{"url": "https://api.elis.rossum.ai/v1/documents/12345"}]}

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

OUTPUT_FILE = "output.json"


@mock.patch("time.sleep")
@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestExtractData:
    def test_get_data(self, mock_sleep, requests_mock, isolated_cli_runner):
        with open("empty_page.pdf", "wb") as f:
            f.write(_EMPTY_PDF_FILE)

        with open("empty_img.png", "wb") as f:
            f.write(_EMPTY_PNG_FILE)

        requests_mock.post(
            UPLOAD_ENDPOINT,
            [
                {
                    "json": {"results": [{"annotation": ANNOTATION_TO_REVIEW}]},
                    "headers": {"Authorization": f"Token {TOKEN}"},
                    "status_code": 201,
                },
                {
                    "json": {"results": [{"annotation": ANNOTATION_FAILED}]},
                    "headers": {"Authorization": f"Token {TOKEN}"},
                    "status_code": 201,
                },
            ],
        )

        requests_mock.get(
            re.compile(fr"{ANNOTATIONS_URL}/\d"),
            [
                {"json": {"url": ANNOTATION_TO_REVIEW, "status": "importing"}, "status_code": 200},
                {"json": {"url": ANNOTATION_TO_REVIEW, "status": "to_review"}, "status_code": 200},
            ],
        )

        requests_mock.get(
            EXPORT_ENDPOINT,
            json=OUTPUT_JSON,
            request_headers={"Authorization": f"Token {TOKEN}"},
            complete_qs=True,
            status_code=200,
        )

        result = isolated_cli_runner.invoke(
            get_data, [QUEUE_ID, "empty_img.png", "empty_page.pdf", "-O", OUTPUT_FILE]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert (
            result.output
            == f".Processing of the annotation at {ANNOTATIONS_URL}/{ANNOTATION_TO_REVIEW_ID} "
            f"finished.\nProcessing of the annotation at "
            f"{ANNOTATIONS_URL}/{ANNOTATION_TO_REVIEW_ID} finished.\n"
        )
        mock_sleep.assert_called_once()
