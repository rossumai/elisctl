import configparser
from pathlib import Path
from textwrap import dedent
from traceback import print_tb

import pytest
from click import ClickException

from elisctl import configure


class TestConfigure:
    def test_file_created(self, isolated_cli_runner, configuration_path):
        expected_credentials = {
            "url": "mock://some.example.com",
            "username": "some_username",
            "password": "secret%",
        }
        result = isolated_cli_runner.invoke(
            configure.cli,
            input=dedent(
                f"""\
                {expected_credentials["url"]}
                {expected_credentials["username"]}
                {expected_credentials["password"]}
                """
            ),
        )
        assert not result.exit_code, print_tb(result.exc_info[2])

        config = configparser.RawConfigParser()
        config.read(configuration_path)

        assert expected_credentials == config["default"]

    def test_profile_added(self, isolated_cli_runner, configuration_path):
        expected_credentials = {
            "url": "mock://some.example.com",
            "username": "some_username",
            "password": "secret%",
        }
        result = isolated_cli_runner.invoke(
            configure.cli,
            ["--profile", "new_profile"],
            input=dedent(
                f"""\
                    {expected_credentials["url"]}
                    {expected_credentials["username"]}
                    {expected_credentials["password"]}
                    """
            ),
        )
        assert not result.exit_code, print_tb(result.exc_info[2])

        config = configparser.RawConfigParser()
        config.read(configuration_path)

        assert expected_credentials == config["new_profile"]


    @pytest.mark.runner_setup(env={"ELIS_TEST": "test"})
    def test_get_credential_from_env(self, isolated_cli_runner):
        with isolated_cli_runner.isolation():
            result = configure.get_credential("test")
        assert "test" == result

    @pytest.mark.runner_setup(env={"ELIS_PROFILE": "test_profile"})
    def test_get_credential_from_env_profile(self, isolated_cli_runner, configuration_path):
        with isolated_cli_runner.isolation():
            configuration_path.parent.mkdir()

            config = configparser.RawConfigParser()
            config["test_profile"] = {"test": "test%"}
            with configuration_path.open("w") as f:
                config.write(f)

            result = configure.get_credential("test")
        assert "test%" == result

    '''
        Test credentials from config file given profile
    '''
    def test_get_credential_from_file_given_profile(self, isolated_cli_runner, configuration_path):
        with isolated_cli_runner.isolation():
            configuration_path.parent.mkdir()

            config = configparser.RawConfigParser()
            config["test_profile"] = {"test": "test%"}
            with configuration_path.open("w") as f:
                config.write(f)

            result = configure.get_credential("test", "test_profile")
        assert "test%" == result

    def test_get_credential_from_file(self, isolated_cli_runner, configuration_path):
        with isolated_cli_runner.isolation():
            configuration_path.parent.mkdir()

            config = configparser.RawConfigParser()
            config["default"] = {"test": "test%"}
            with configuration_path.open("w") as f:
                config.write(f)

            result = configure.get_credential("test")
        assert "test%" == result

    @pytest.mark.usefixtures("configuration_path")
    def test_no_credentials(self):
        with pytest.raises(ClickException) as e:
            configure.get_credential("test")

        assert e.value.message == (
            "Provide API credential test. "
            "Either by using `elisctl configure`, or environment variable ELIS_TEST."
        )


@pytest.fixture
@pytest.mark.usefixtures("isolated_cli_runner")
def configuration_path():
    old_path = configure.CONFIGURATION_PATH
    new_path = Path(".elis") / "credentials"
    configure.CONFIGURATION_PATH = new_path
    yield new_path
    configure.CONFIGURATION_PATH = old_path
