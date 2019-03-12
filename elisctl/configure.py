import configparser
import os
from pathlib import Path

import click

CONFIGURATION_PATH = Path.home() / ".elis" / "credentials"
DEFAULT_ELIS_URL = "https://api.elis.rossum.ai"

HELP = f"""\
Configure API setup.

Credentials are saved into {CONFIGURATION_PATH}. Alternatively, configuration can be set using
environment variables:

ELIS_URL: URL of the API (e.g. {DEFAULT_ELIS_URL})
ELIS_USERNAME: username of an ELIS account
ELIS_PASSWORD: password to the ELIS account
"""


@click.command(name="configure", help=HELP)
def cli():
    config = configparser.RawConfigParser()
    config["default"] = {
        "url": click.prompt(f"API URL", default=DEFAULT_ELIS_URL, type=str).strip().rstrip("/"),
        "username": click.prompt(f"Username", type=str).strip(),
        "password": click.prompt(f"Password", hide_input=True, type=str).strip(),
    }
    CONFIGURATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIGURATION_PATH.open("w") as f:
        config.write(f)


def get_credential(attr: str) -> str:
    res = os.getenv(f"ELIS_{attr.upper()}")
    if res is not None:
        return res

    config = configparser.RawConfigParser()
    config.read(CONFIGURATION_PATH)
    try:
        config_dict = config["default"]
    except KeyError as e:
        raise click.ClickException(
            f"Provide API credential {attr}. "
            f"Either by using `elisctl configure`, or environment variable ELIS_{attr.upper()}."
        ) from e
    else:
        res = config_dict.get(attr)
    assert res is not None
    return res.strip()
