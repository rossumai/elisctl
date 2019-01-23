import json
from copy import deepcopy
from traceback import print_tb

import pytest

from elisctl.schema import transform

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
            transform.cli, [SCHEMA_NAME, "substitute-options", "vat_rate", OPTIONS_NAME]
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["options"] = OPTIONS
        assert new_schema == json.loads(result.stdout)

    def test_change(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, [SCHEMA_NAME, "change", "vat_rate", f"options={json.dumps(OPTIONS)}"]
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["options"] = OPTIONS
        assert new_schema == json.loads(result.stdout)

    def test_change_all_datapoints(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli,
            [SCHEMA_NAME, "change", "ALL", "-c", "datapoint", 'constraints={"required":true}'],
        )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["constraints"] = {"required": True}
        new_schema[1]["children"][1]["constraints"] = {"required": True}
        assert new_schema == json.loads(result.stdout)

    def test_remove(self, isolated_cli_runner):
        with open(SCHEMA_NAME, "w") as schema:
            json.dump(ORIGINAL_SCHEMA, schema)

        result = isolated_cli_runner.invoke(transform.cli, [SCHEMA_NAME, "remove", "vat_rate"])
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"] = []
        assert new_schema == json.loads(result.stdout)

    def test_move(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, [SCHEMA_NAME, "move", "vat_rate", "other"]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[1]["children"].append(new_schema[0]["children"].pop())
        assert new_schema == json.loads(result.stdout)

    def test_add(self, isolated_cli_runner):
        result = isolated_cli_runner.invoke(
            transform.cli, [SCHEMA_NAME, "add", "basic_info", "id=test"]
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
            transform.cli, [SCHEMA_NAME, "add", "other", "id=test", "--place-before", "desc"]
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
            transform.cli, [SCHEMA_NAME, "add", "test_multi", "id=test"]
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
            transform.cli, [SCHEMA_NAME, "wrap-in-multivalue", "desc"]
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


@pytest.fixture
def _original_schema_file(isolated_cli_runner):
    with open(SCHEMA_NAME, "w") as schema:
        json.dump(ORIGINAL_SCHEMA, schema)
    yield
