from io import StringIO
from pathlib import Path
from traceback import print_tb

import pandas as pd

from rossumctl.tools import xls_to_csv

FILENAME = "some.xls"
DATA = """\
1;abc
2;cde
3;fgh\
"""


class TestXLSToCSV:
    def test_success(self, isolated_cli_runner):
        with StringIO() as csv, open(FILENAME, "wb") as xls:
            csv.write(DATA)
            csv.seek(0)
            df = pd.read_csv(csv, sep=";", names=["value", "label"], header=None, dtype=(str, str))
            df.to_excel(xls, index=False)

        result = isolated_cli_runner.invoke(xls_to_csv.cli, [FILENAME, "--header", "0"])
        assert not result.exit_code
        assert DATA == result.stdout.strip()

    def test_output_to_file(self, isolated_cli_runner):
        output_file = Path("test.csv")
        with StringIO() as csv, open(FILENAME, "wb") as xls:
            csv.write(DATA)
            csv.seek(0)
            df = pd.read_csv(csv, sep=";", names=["value", "label"], header=None, dtype=(str, str))
            df.to_excel(xls, index=False)

        result = isolated_cli_runner.invoke(
            xls_to_csv.cli, [FILENAME, "--header", "0", "-O", str(output_file)]
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert DATA == output_file.read_text().rstrip("\n")

    def test_order_columns(self, isolated_cli_runner):
        with StringIO() as csv, open(FILENAME, "wb") as xls:
            csv.write("\n".join(";".join(reversed(row.split(";"))) for row in DATA.split("\n")))
            csv.seek(0)
            df = pd.read_csv(csv, sep=";", names=["label", "value"], header=None, dtype=(str, str))
            df.to_excel(xls, index=False)

        result = isolated_cli_runner.invoke(
            xls_to_csv.cli, [FILENAME, "--header", "0", "--value", "1", "--label", "0"]
        )
        assert not result.exit_code
        assert DATA == result.stdout.strip()
