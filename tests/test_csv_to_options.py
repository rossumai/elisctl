import json
from pathlib import Path

from elisctl.tools import csv_to_options

FILENAME = "some.csv"
DATA = [
    {"value": "1", "label": "1: abc"},
    {"value": "2", "label": "2: cde"},
    {"value": "3", "label": "3: fgh"},
]


class TestCSVToOptions:
    def test_no_header(self, isolated_cli_runner):
        with open(FILENAME, "w") as f:
            for line in DATA:
                f.write(f"{line['value']},{line['label'].split(' ')[1]}\n")

        result = isolated_cli_runner.invoke(
            csv_to_options.cli, [FILENAME, "--delimiter", ",", "--add-value"]
        )
        assert not result.exit_code

        d = json.loads(result.stdout)
        assert DATA == d

    def test_no_header_output_file(self, isolated_cli_runner):
        output_file = Path("test.json")

        with open(FILENAME, "w") as f:
            for line in DATA:
                f.write(f"{line['value']},{line['label'].split(' ')[1]}\n")

        result = isolated_cli_runner.invoke(
            csv_to_options.cli,
            [FILENAME, "--delimiter", ",", "--add-value", "-O", str(output_file)],
        )
        assert not result.exit_code
        assert DATA == json.loads(output_file.read_text())

    def test_header(self, isolated_cli_runner):
        with open(FILENAME, "w") as f:
            f.write(f"value;label\n")
            for line in DATA:
                f.write(f"{line['value']};{line['label'].split(' ')[1]}\n")

        result = isolated_cli_runner.invoke(
            csv_to_options.cli, [FILENAME, "--header", "0", "--add-value"]
        )
        assert not result.exit_code

        d = json.loads(result.stdout)
        assert DATA == d
