#!/usr/bin/env python3
import warnings
from copy import deepcopy
from typing import List, Callable, Optional, Tuple, Set

import click as click

from elisctl.lib import DataPointDict, DataPoints


def traverse_datapoints(
    datapoints: List[dict], transformation: Callable, parent_categories: List[str] = None, **kwargs
) -> List[dict]:
    dummy_root = {"category": "root", "id": None, "children": datapoints}
    return _traverse_datapoints([dummy_root], transformation, parent_categories, **kwargs)[0][
        "children"
    ]


def _traverse_datapoints(
    datapoints: List[dict], transformation: Callable, parent_categories: List[str] = None, **kwargs
) -> List[dict]:
    new_datapoints = []
    parent_categories = parent_categories or []
    for datapoint in datapoints:
        new_datapoint = deepcopy(datapoint)
        category = datapoint["category"]
        if category != "datapoint":
            parent_categories_ = parent_categories[:] + [category]
            children = new_datapoint.pop("children", [])
            if category == "multivalue" and children:
                [new_datapoint["children"]] = _traverse_datapoints(
                    [children], transformation, parent_categories_, **kwargs
                )
            elif category == "multivalue":
                new_datapoint["children"] = None
            elif category in ("tuple", "section", "root"):
                new_datapoint["children"] = _traverse_datapoints(
                    children, transformation, parent_categories_, **kwargs
                )
        new_datapoint = transformation(new_datapoint, parent_categories, **kwargs)
        if new_datapoint:
            new_datapoints.append(new_datapoint)

    return new_datapoints


def substitute_options(
    datapoint: DataPointDict, parent_categories: List[str], id_: str, options: List[dict]
) -> DataPointDict:
    if (
        datapoint["category"] != "datapoint"
        or datapoint["type"] != "enum"
        or datapoint["id"] != id_
    ):
        return datapoint

    new_datapoint = deepcopy(datapoint)
    return {**new_datapoint, "options": options}


def remove(
    datapoint: DataPointDict, parent_categories: List[str], ids: Tuple[str, ...]
) -> Optional[DataPointDict]:
    if datapoint["id"] in ids:
        if parent_categories and "multivalue" == parent_categories[-1]:
            warnings.warn("Cannot delete child of a multivalue.")
            return datapoint
        else:
            return None
    else:
        return datapoint


def wrap_in_multivalue(
    datapoint: DataPointDict, parent_categories: List[str], exclude_ids: Set[str]
) -> DataPointDict:
    if (
        "multivalue" in parent_categories
        or datapoint["category"] in ("multivalue", "section", "root")
        or datapoint["id"] in exclude_ids
    ):
        return datapoint
    return {
        "id": f'{datapoint["id"]}_multi',
        "label": datapoint["label"],
        "children": {"use_rir_content": True, **datapoint},
        "category": "multivalue",
        "max_occurrences": None,
        "min_occurrences": None,
    }


def add(
    datapoint: dict,
    parent_categories: List[str],
    parent_id: str,
    datapoint_to_add: DataPointDict,
    place_before: Optional[str] = None,
) -> dict:
    if datapoint["id"] != parent_id:
        return datapoint

    if datapoint["category"] in ("tuple", "section", "root"):
        new_datapoint = deepcopy(datapoint)
        if place_before is None:
            new_datapoint["children"].append(datapoint_to_add)
        else:
            new_datapoint["children"].insert(
                _find_index_of_id(place_before, new_datapoint["children"]), datapoint_to_add
            )
        return new_datapoint
    elif datapoint["category"] == "multivalue" and not datapoint.get("children"):
        new_datapoint = deepcopy(datapoint)
        new_datapoint["children"] = datapoint_to_add
        return new_datapoint
    elif datapoint["category"] == "multivalue":
        warnings.warn("Cannot add child to a filled multivalue.")
        return datapoint
    else:
        return datapoint


def _find_index_of_id(id_: str, children: DataPoints) -> int:
    for i, child in enumerate(children):
        if child["id"] == id_:
            return i
    else:
        raise click.ClickException(f"Not found ID '{id_}' to place behind.")


def change(
    datapoint: DataPointDict,
    parent_categories: List[str],
    id_: str,
    to_change: DataPointDict,
    filtered_categories: Tuple[str],
) -> DataPointDict:
    is_of_id = id_ in (datapoint["id"], "ALL")
    is_of_category = not filtered_categories or datapoint["category"] in filtered_categories
    if not (is_of_id and is_of_category):
        return datapoint
    else:
        return {**datapoint, **to_change}


def get(datapoints: List[dict], id_: str) -> Optional[dict]:
    res = None

    for datapoint in datapoints:
        if datapoint["id"] == id_:
            return datapoint

        category = datapoint["category"]
        if category in ("section", "tuple"):
            res = get(datapoint["children"], id_)
        elif category == "multivalue":
            res = get([datapoint["children"]], id_)
        if res is not None:
            return res
    return res


def _new_datapoint(datapoint_to_add: DataPointDict) -> DataPointDict:
    try:
        id_ = datapoint_to_add.pop("id")
    except KeyError as e:
        raise click.BadArgumentUsage("Missing key 'id'.") from e

    category = datapoint_to_add.pop("category", "datapoint")
    default = {"id": id_, "label": id_}
    if category == "datapoint":
        default = {**default, "rir_field_names": [], **_new_singlevalue(datapoint_to_add)}
    elif category == "multivalue":
        default = {
            **default,
            "children": None,
            "default_value": None,
            "min_occurrences": None,
            "max_occurrences": None,
        }
    elif category == "tuple":
        default = {**default, "rir_field_names": [], "children": []}
    elif category == "section":
        raise click.BadArgumentUsage("Cannot add section.")
    else:
        raise click.BadArgumentUsage("Unknown category.")
    return {**default, **datapoint_to_add, "category": category}


def _new_singlevalue(datapoint_to_add: DataPointDict) -> DataPointDict:
    type_ = datapoint_to_add.pop("type", "string")
    default: DataPointDict = {
        "width_chars": 10,
        "default_value": None,
        "constraints": {"required": False},
    }
    if type_ == "enum":
        default = {**default, "options": [{"value": "0", "label": "---"}]}
    elif type_ == "date":
        default = {**default, "format": "D. M. YYYY"}
    elif type_ == "number":
        default = {**default, "format": "# ##0.#"}
    elif type_ != "string":
        raise click.BadArgumentUsage("Unknown type.")

    return {**default, "type": type_}
