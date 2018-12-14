from __future__ import annotations

import os
import urllib.parse
from contextlib import AbstractContextManager
from typing import Dict, List, Tuple, Optional

import click
import requests
from requests import Response

DEFAULT_ELIS_URL = "https://api.elis.rossum.ai"
DEFAULT_ELIS_ADMIN = "support@rossum.ai"


class APIClient(AbstractContextManager):
    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_api_version: bool = True,
        auth_using_token: bool = True,
    ):
        self._url = url
        self._user = user
        self._password = password
        self._use_api_version = use_api_version
        self._auth_using_token = auth_using_token

        self._token: Optional[str] = None

    def __enter__(self) -> APIClient:  # noqa: F821
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.logout()

    @classmethod
    def csv(
        cls, url: str = None, user: str = None, password: str = None
    ) -> APIClient:  # noqa: F821
        return cls(url, user, password, False, False)

    def _get_api_credentials(self) -> None:
        self._url: str = (
            self._url
            or os.getenv("ADMIN_API_URL")
            or click.prompt(f"API URL", default=DEFAULT_ELIS_URL, type=str)
        ).strip("/ ")
        self._user: str = (
            self._user
            or os.getenv("ADMIN_API_LOGIN")
            or click.prompt(f"Superadmin login", default=DEFAULT_ELIS_ADMIN, type=str)
        ).strip()
        self._password: str = (
            self._password
            or os.getenv("ADMIN_API_PASSWORD")
            or click.prompt(f"Superadmin password", hide_input=True, type=str)
        ).strip()

    @property
    def user(self) -> str:
        if self._user is None:
            self._get_api_credentials()
            assert self._user is not None
        return self._user

    @property
    def password(self) -> str:
        if self._password is None:
            self._get_api_credentials()
            assert self._password is not None
        return self._password

    @property
    def url(self) -> str:
        if self._url is None:
            self._get_api_credentials()
        return f'{self._url}{"/v1" if self._use_api_version else ""}'

    @property
    def token(self) -> str:
        if self._token is None:
            response = requests.post(
                f"{self.url}/auth/login", json={"username": self.user, "password": self.password}
            )
            assert response.ok
            self._token = response.json()["key"]

        return self._token

    def post(self, path: str, data: dict, expected_status_code: int = 201) -> Response:
        return self._request_url(
            "post", f"{self.url}/{path}", json=data, expected_status_code=expected_status_code
        )

    def get(self, path: str, query: dict = None) -> Response:
        return self._request_url("get", f"{self.url}/{path}", query)

    def get_url(self, url: str, query: dict = None) -> Response:
        return self._request_url("get", url, query)

    def delete_url(self, url: str) -> Response:
        return self._request_url("delete", url, expected_status_code=204)

    def _request_url(
        self, method: str, url: str, query: dict = None, expected_status_code: int = 200, **kwargs
    ) -> Response:
        url_with_query = url + "?" + urllib.parse.urlencode(query, doseq=True) if query else url
        response = requests.request(method, url_with_query, **self._authentication, **kwargs)
        if response.status_code != expected_status_code:
            raise click.ClickException(f"Invalid response [{url_with_query}]: {response.text}")
        return response

    def delete(self, to_delete: Dict[str, str], verbose: int = 0, item: str = "annotation") -> None:
        for id_, url in to_delete.items():
            try:
                self.delete_url(url)
            except click.ClickException as exc:
                click.echo(f'Deleting {item} {id_} caused "{exc}".')
            except Exception as exc:
                click.echo(f'Deleting {item} {id_} caused an unexpected excpetion: "{exc}".')
                raise click.ClickException(str(exc))
            else:
                if verbose > 1:
                    click.echo(f"Deleted {item} {id_}.")

    def get_paginated(self, path: str, query: Dict[str, str]) -> Tuple[List[dict], int]:
        response = self.get(path, query)
        response_dict = response.json()

        res = response_dict["results"]
        next_page = response_dict["pagination"]["next"]

        while next_page:
            response = self.get_url(next_page)
            response_dict = response.json()

            res.extend(response_dict["results"])
            next_page = response_dict["pagination"]["next"]

        return res, response_dict["pagination"]["total"]

    @property
    def _authentication(self) -> dict:
        if self._auth_using_token:
            return {"headers": {"Authorization": "Token " + self.token}}
        else:
            return {"auth": (self.user, self.password)}

    def logout(self) -> None:
        if self._auth_using_token:
            self.post("auth/logout", {}, expected_status_code=200)


def get_json(response: Response) -> dict:
    try:
        return response.json()
    except ValueError as e:
        raise click.ClickException(f"Invalid JSON [{response.url}]: {response.text}") from e


def get_text(response: Response) -> str:
    try:
        return response.text
    except ValueError as e:
        raise click.ClickException(f"Invalid text [{response.url}]: {response.text}") from e
