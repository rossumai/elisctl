from __future__ import annotations

import urllib.parse
from contextlib import AbstractContextManager
from typing import Dict, List, Tuple, Optional, Iterable, Any

import click
import requests
from requests import Response

from elisctl.configure import get_credential


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

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.logout()

    @classmethod
    def csv(
        cls, url: str = None, user: str = None, password: str = None
    ) -> APIClient:  # noqa: F821
        return cls(url, user, password, False, False)

    @property
    def user(self) -> str:
        if self._user is None:
            self._user = get_credential("username")
        return self._user

    @property
    def password(self) -> str:
        if self._password is None:
            self._password = get_credential("password")
        return self._password

    @property
    def url(self) -> str:
        if self._url is None:
            _url = get_credential("url").rstrip("/")
            self._url = f'{_url}{"/v1" if self._use_api_version else ""}'
        return self._url

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

    def patch(self, path: str, data: dict) -> Response:
        return self._request_url("patch", f"{self.url}/{path}", json=data)

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
                click.echo(f'Deleting {item} {id_} caused an unexpected exception: "{exc}".')
                raise click.ClickException(str(exc))
            else:
                if verbose > 1:
                    click.echo(f"Deleted {item} {id_}.")

    def get_paginated(
        self, path: str, query: Optional[Dict[str, str]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
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

    def _sideload(
        self, objects: List[dict], sideloads: Optional[Iterable[str]] = None
    ) -> List[dict]:
        for sideload in sideloads or []:
            sideloaded, _ = self.get_paginated(sideload)
            sideloaded_dicts = {
                sideloaded_dict["url"]: sideloaded_dict for sideloaded_dict in sideloaded
            }
            key = sideload.rstrip("es")

            def inject_sideloaded(obj: dict) -> dict:
                try:
                    url = obj[key]
                except KeyError:
                    obj[sideload] = [sideloaded_dicts[url] for url in obj[sideload]]
                else:
                    obj[key] = sideloaded_dicts[url]
                return obj

            objects = [inject_sideloaded(o) for o in objects]
        return objects

    @property
    def _authentication(self) -> dict:
        if self._auth_using_token:
            return {"headers": {"Authorization": "Token " + self.token}}
        else:
            return {"auth": (self.user, self.password)}

    def logout(self) -> None:
        if self._auth_using_token:
            self.post("auth/logout", {}, expected_status_code=200)


class ELISClient(APIClient):
    def get_organization(self, organization_id: Optional[int] = None) -> dict:
        if organization_id is None:
            user_url = get_json(self.get("auth/user"))["url"]
            organization_url = get_json(self.get_url(user_url))["organization"]
            res = self.get_url(organization_url)
        else:
            res = self.get(f"organizations/{organization_id}")
        return get_json(res)

    def get_workspaces(self, sideloads: Optional[Iterable[str]] = None) -> List[dict]:
        workspaces, _ = self.get_paginated("workspaces")
        self._sideload(workspaces, sideloads)
        return workspaces


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
