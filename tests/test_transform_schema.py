import json
from copy import deepcopy

from click.testing import CliRunner

from tools import transform_schema

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
    }
]
OPTIONS = [
    {"value": "1", "label": "1: abc"},
    {"value": "2", "label": "2: cde"},
    {"value": "3", "label": "3: fgh"},
]


class TestTransformSchema:
    def test_substitute_options(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open(OPTIONS_NAME, "w") as options, open(SCHEMA_NAME, "w") as schema:
                json.dump(ORIGINAL_SCHEMA, schema)
                json.dump(OPTIONS, options)

            result = runner.invoke(
                transform_schema.cli,
                [SCHEMA_NAME, "substitute-options", "--id", "vat_rate", OPTIONS_NAME],
            )
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"][0]["options"] = OPTIONS
        assert new_schema == json.loads(result.stdout)

    def test_remove(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open(SCHEMA_NAME, "w") as schema:
                json.dump(ORIGINAL_SCHEMA, schema)

            result = runner.invoke(transform_schema.cli, [SCHEMA_NAME, "remove", "vat_rate"])
        assert not result.exit_code
        new_schema = deepcopy(ORIGINAL_SCHEMA)
        new_schema[0]["children"] = []
        assert new_schema == json.loads(result.stdout)
