import json

from click.testing import CliRunner

from tools import csv_to_options


FILENAME = "some.csv"
DATA = [
    {"value": "1", "label": "1: abc"},
    {"value": "2", "label": "2: cde"},
    {"value": "3", "label": "3: fgh"},
]


class TestCSVToOptions:
    def test_no_header(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open(FILENAME, "w") as f:
                for line in DATA:
                    f.write(f"{line['value']},{line['label'].split(' ')[1]}\n")

            result = runner.invoke(
                csv_to_options.cli, [FILENAME, "--delimiter", ",", "--add-value"]
            )
        assert not result.exit_code

        d = json.loads(result.stdout)
        assert DATA == d

    def test_header(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open(FILENAME, "w") as f:
                f.write(f"value;label\n")
                for line in DATA:
                    f.write(f"{line['value']};{line['label'].split(' ')[1]}\n")

            result = runner.invoke(csv_to_options.cli, [FILENAME, "--header", "0", "--add-value"])
        assert not result.exit_code

        d = json.loads(result.stdout)
        assert DATA == d
