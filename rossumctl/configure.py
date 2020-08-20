import configparser
import os
from typing import Optional

from pathlib import Path

import click

from rossumctl import CTX_PROFILE, CTX_DEFAULT_PROFILE

CONFIGURATION_PATH = Path.home() / ".rossum" / "credentials"
DEFAULT_ROSSUM_URL = "https://api.elis.rossum.ai"


ROSSUM_ENV_PROFILE_VAR = "ROSSUM_PROFILE"


HELP = f"""\
Configure API setup.

Credentials are saved into {CONFIGURATION_PATH}.
It is possible to add new or update existing profile by writing down the profile name.
If no profile is chosen, credentials are set to default profile.

Alternatively, configuration can be set using
environment variables:

ROSSUM_URL: URL of the API (e.g. {DEFAULT_ROSSUM_URL})
ROSSUM_USERNAME: username of an ROSSUM account
ROSSUM_PASSWORD: password to the ROSSUM account
"""


@click.command(name="configure", help=HELP)
@click.pass_context
def cli(ctx: click.Context,):
    config = configparser.RawConfigParser()

    if os.path.isfile(CONFIGURATION_PATH):
        with CONFIGURATION_PATH.open("r") as f:
            config.read_file(f)

    config[ctx.obj[CTX_PROFILE]] = {
        "url": click.prompt(f"API URL", default=DEFAULT_ROSSUM_URL, type=str).strip().rstrip("/"),
        "username": click.prompt(f"Username", type=str).strip(),
        "password": click.prompt(f"Password", hide_input=True, type=str).strip(),
    }

    CONFIGURATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIGURATION_PATH.open("w") as f:
        config.write(f)


def get_credential(attr: str, profile: Optional[str] = None) -> str:
    res = os.getenv(f"ROSSUM_{attr.upper()}")
    if res is not None:
        return res

    profile = os.getenv(ROSSUM_ENV_PROFILE_VAR) or profile or CTX_DEFAULT_PROFILE

    config = configparser.RawConfigParser()
    config.read(CONFIGURATION_PATH)
    try:
        config_dict = config[profile]
    except KeyError as e:
        raise click.ClickException(
            f"Provide API credential {attr}. "
            f"Either by using `rossumctl configure`, or environment variable ROSSUM_{attr.upper()}."
        ) from e
    else:
        res = config_dict.get(attr)
    assert res is not None
    return res.strip()
