import configparser
import os
from pathlib import Path

import click

CONFIGURATION_PATH = Path.home() / ".elis" / "credentials"
DEFAULT_ELIS_URL = "https://api.elis.rossum.ai"


DEFAULT_PROFILE = "default"
ELIS_ENV_PROFILE_VAR = "ELIS_PROFILE"


HELP = f"""\
Configure API setup.

Credentials are saved into {CONFIGURATION_PATH}. 
It is possible to add new or update existing profile by writing down the profile name. If no profile is chosen,
credentials are set to default profile.

Alternatively, configuration can be set using
environment variables:

ELIS_URL: URL of the API (e.g. {DEFAULT_ELIS_URL})
ELIS_USERNAME: username of an ELIS account
ELIS_PASSWORD: password to the ELIS account
"""


@click.command(name="configure", help=HELP)
@click.option('--profile', default=DEFAULT_PROFILE, help='profile_name')
def cli(profile):
    config = configparser.RawConfigParser()

    if os.path.isfile(CONFIGURATION_PATH):
        with CONFIGURATION_PATH.open("r") as f:
            config.read_file(f)

    config[profile] = {
        "url": click.prompt(f"API URL", default=DEFAULT_ELIS_URL, type=str).strip().rstrip("/"),
        "username": click.prompt(f"Username", type=str).strip(),
        "password": click.prompt(f"Password", hide_input=True, type=str).strip()
    }

    CONFIGURATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIGURATION_PATH.open("w") as f:
        config.write(f)


def get_credential(attr: str, profile=None) -> str:
    res = os.getenv(f"ELIS_{attr.upper()}")
    if res is not None:
        return res

    if profile is None: # input profile was not set by parametr
        l_profile = os.getenv(ELIS_ENV_PROFILE_VAR) # try to get env var profile
        if l_profile is None:
            l_profile = DEFAULT_PROFILE # set default profile
    else:
        l_profile = profile

    config = configparser.RawConfigParser()
    config.read(CONFIGURATION_PATH)
    try:
        config_dict = config[l_profile]
    except KeyError as e:
        raise click.ClickException(
            f"Provide API credential {attr}. "
            f"Either by using `elisctl configure`, or environment variable ELIS_{attr.upper()}."
        ) from e
    else:
        res = config_dict.get(attr)
    assert res is not None
    return res.strip()
