from traceback import print_tb

from elisctl.main import entry_point


class TestEntryPoint:
    def test_shell(self, cli_runner):
        result = cli_runner.invoke(entry_point)
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output.rstrip("\n").endswith("elis> ")
