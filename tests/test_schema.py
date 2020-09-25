import json
from copy import deepcopy
from pathlib import Path
from traceback import print_tb

import pytest

from rossumctl.schema.transform import commands as transform
from rossumctl.schema.commands import download_command, list_command
from tests.conftest import SCHEMAS_URL, QUEUES_URL, TOKEN

SCHEMA_NAME = "schema.json"
OPTIONS_NAME = "options.json"
ORIGINAL_SCHEMA = [
    {
        "category": "section",
        "id": "basic_info",
        "label": "Basic info",
        "icon": "man_with_a_hat",
        "children": [
            {
                "category": "datapoint",
                "id": "vat_rate",
                "type": "enum",
                "label": "Rate",
                "width_chars": 2,
                "rir_field_names": [],
                "default_value": "high",
                "options": [],
            }
        ],
    },
    {
        "category": "section",
        "id": "other",
        "label": "Other",
        "icon": "questionmark",
        "children": [
            {
                "category": "multivalue",
                "id": "test_multi",
                "label": "test",
                "children": None,
                "default_value": None,
                "min_occurrences": None,
                "max_occurrences": None,
            },
            {
                "category": "datapoint",
                "id": "desc",
                "type": "string",
                "label": "Description",
                "width_chars": 10,
                "rir_field_names": [],
                "default_value": None,
            },
        ],
    },
]
OPTIONS = [
    {"value": "1", "label": "1: abc"},
    {"value": "2", "label": "2: cde"},
    {"value": "3", "label": "3: fgh"},
]


@pytest.mark.usefixtures("_original_schema_file")
class TestTransformSchema:
    def test_substitute_options(self, isolated_cli_runner):
        with open(OPTIONS_NAME, "w") as options:
            json.dump(OPTIONS, options)

        result = isolated_cli_runner.invoke(
            transform.cli, ["substitute-options", SCHEMA_NAME, "vat_rate", OPTIONS_NAME]
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["options"] = OPTIONS
        assert new_schema == json.loads(result.stdout)

    def test_change(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, ["change", SCHEMA_NAME, "vat_rate", f"options={json.dumps(OPTIONS)}"]
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["options"] = OPTIONS
        assert new_schema == json.loads(result.stdout)

    def test_change_all_datapoints(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli,
            ["change", SCHEMA_NAME, "ALL", "-c", "datapoint", 'constraints={"required":true}'],
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["constraints"] = {"required": True}
        new_schema[1]["children"][1]["constraints"] = {"required": True}
        assert new_schema == json.loads(result.stdout)

    def test_remove(self, isolated_cli_runner):
        with open(SCHEMA_NAME, "w") as schema:
            json.dump(ORIGINAL_SCHEMA, schema)

        result = isolated_cli_runner.invoke(transform.cli, ["remove", SCHEMA_NAME, "vat_rate"])
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"] = []
        assert new_schema == json.loads(result.stdout)

    def test_move(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, ["move", SCHEMA_NAME, "vat_rate", "other"]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[1]["children"].append(new_schema[0]["children"].pop())
        assert new_schema == json.loads(result.stdout)

    def test_output_file(self, isolated_cli_runner):
        output_file = Path("test.csv")

        # Arbitrarily chosen move command. It should work everywhere else the same way.
        result = isolated_cli_runner.invoke(
            transform.cli, ["-O", str(output_file), "move", SCHEMA_NAME, "vat_rate", "other"]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[1]["children"].append(new_schema[0]["children"].pop())
        assert new_schema == json.loads(output_file.read_text())

    def test_add(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, ["add", SCHEMA_NAME, "basic_info", "id=test"]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"].append(
            {
                "category": "datapoint",
                "constraints": {"required": False},
                "default_value": None,
                "id": "test",
                "label": "test",
                "rir_field_names": [],
                "type": "string",
                "width_chars": 10,
            }
        )
        assert new_schema == json.loads(result.stdout)

    def test_add_place_before(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, ["add", SCHEMA_NAME, "other", "id=test", "--place-before", "desc"]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[1]["children"].insert(
            1,
            {
                "category": "datapoint",
                "constraints": {"required": False},
                "default_value": None,
                "id": "test",
                "label": "test",
                "rir_field_names": [],
                "type": "string",
                "width_chars": 10,
            },
        )
        assert new_schema == json.loads(result.stdout)

    def test_add_single_to_empty_multivalue(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, ["add", SCHEMA_NAME, "test_multi", "id=test"]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[1]["children"][0]["children"] = {
            "category": "datapoint",
            "constraints": {"required": False},
            "default_value": None,
            "id": "test",
            "label": "test",
            "rir_field_names": [],
            "type": "string",
            "width_chars": 10,
        }
        assert new_schema == json.loads(result.stdout)

    def test_wrap_in_multivalue(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, ["wrap-in-multivalue", SCHEMA_NAME, "desc"]
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        single_value = new_schema[0]["children"].pop()
        new_schema[0]["children"].append(
            {
                "id": f'{single_value["id"]}_multi',
                "label": single_value["label"],
                "children": {"use_rir_content": True, **single_value},
                "category": "multivalue",
                "max_occurrences": None,
                "min_occurrences": None,
            }
        )
        assert new_schema == json.loads(result.stdout)

    def test_help_without_args_in_parent(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(transform.cli, ["add", "--help"])
        assert not result.exit_code, print_tb(result.exc_info[2])


@pytest.fixture
def _original_schema_file(isolated_cli_runner):
    with open(SCHEMA_NAME, "w") as schema:
        json.dump(ORIGINAL_SCHEMA, schema)
    yield


schema_id = "1"
schema_content = [{"label": "Příliš žluťoučký kůň úpěl ďábelské ódy."}]


@pytest.mark.usefixtures("mock_login_request", "mock_get_schema", "rossum_credentials")
class TestDownload:
    output_file = Path("test.json")

    def test_stdout(self, cli_runner):
        result = cli_runner.invoke(download_command, [schema_id])
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert schema_content == json.loads(result.stdout)

    def test_output_file(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            download_command, [schema_id, "-O", str(self.output_file)]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert schema_content == json.loads(self.output_file.read_text())


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestList:
    def test_success(self, requests_mock, cli_runner):
        schema_id = 3
        name = "Test schema"
        queue_ids = ["1", "42", "3"]

        queue_urls = [f"{QUEUES_URL}/{id_}" for id_ in queue_ids]

        requests_mock.get(
            SCHEMAS_URL,
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": schema_id, "name": name, "queues": queue_urls}],
            },
        )
        requests_mock.get(
            QUEUES_URL,
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": id_, "url": url} for id_, url in zip(queue_ids, queue_urls)],
            },
        )

        result = cli_runner.invoke(list_command)
        assert not result.exit_code, print_tb(result.exc_info[2])
        expected_table = f"""\
  id  name         queues
----  -----------  --------
   {schema_id}  {name}  {', '.join(queue_ids)}
"""
        assert result.output == expected_table
