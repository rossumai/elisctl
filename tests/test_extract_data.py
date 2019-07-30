import re
from traceback import extract_tb
from typing import Optional
from unittest import mock

import pytest

from elisctl.document.extract_data import get_data
from tests.conftest import (
    ANNOTATIONS_URL,
    API_URL,
    QUEUES_URL,
    TOKEN,
    _EMPTY_PNG_FILE,
    _EMPTY_PDF_FILE,
)

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


def export_endpoint(format_: Optional[str] = None) -> str:
    return f"{QUEUES_URL}/{QUEUE_ID}/export?id={EXPORT_IDS_CHAIN}&format={format_ or 'json'}"


OUTPUT_JSON = {"results": [{"url": "https://api.elis.rossum.ai/v1/documents/12345"}]}

OUTPUT_FILE = "output.json"


@mock.patch("time.sleep")
@pytest.mark.runner_setup(
    env={"ELIS_URL": API_URL, "ELIS_USERNAME": USERNAME, "ELIS_PASSWORD": PASSWORD}
)
@pytest.mark.usefixtures("mock_login_request")
class TestExtractData:
    @pytest.mark.parametrize("format_", [None, "json", "xml", "csv"])
    def test_get_data(self, mock_sleep, requests_mock, isolated_cli_runner, format_):
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
            export_endpoint(format_),
            json=OUTPUT_JSON,
            request_headers={"Authorization": f"Token {TOKEN}"},
            complete_qs=True,
            status_code=200,
        )
        params = [QUEUE_ID, "empty_img.png", "empty_page.pdf", "-O", OUTPUT_FILE]
        if format_:
            params += ["--format", format_]
        result = isolated_cli_runner.invoke(get_data, params)
        assert not result.exit_code, extract_tb(result.exc_info[2])
        assert (
            result.output
            == f".Processing of the annotation at {ANNOTATIONS_URL}/{ANNOTATION_TO_REVIEW_ID} "
            f"finished.\nProcessing of the annotation at "
            f"{ANNOTATIONS_URL}/{ANNOTATION_TO_REVIEW_ID} finished.\n"
        )
        mock_sleep.assert_called_once()
