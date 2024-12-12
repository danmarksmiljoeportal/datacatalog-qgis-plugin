# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from __future__ import annotations

from typing import Union
import os
import tempfile
from datetime import date

from qgis.PyQt.QtCore import QStandardPaths, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import QgsBlockingNetworkRequest

from dmpcatalogue.core.data_classes import (
    WmsSource,
    WmtsSource,
    WfsSource,
    FileSource,
)
from dmpcatalogue.constants import PLUGIN_ICON


def cache_directory(dir_name: str = "dmpcatalogue") -> str:
    """
    Creates cache directory with the given name and returns full path to it.
    """
    dirs = QStandardPaths.standardLocations(
        QStandardPaths.StandardLocation.GenericCacheLocation
    )

    root = dirs[0] if dirs else tempfile.gettempdir()

    cache_dir = os.path.join(root, dir_name)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def file_exists(file_name: str, age: int = 0) -> bool:
    """
    Checks if file file_name exists and it is not older than age day(s).
    """
    if not os.path.exists(file_name):
        return False

    file_date = date.fromtimestamp(os.path.getmtime(file_name))
    delta = date.today() - file_date
    if delta.days > age:
        return False

    return True


def lookup_map(
    data: dict,
    exclude_type: bool = False,
    simplify: bool = False,
    include_resources: bool = False,
) -> dict:
    """
    Transforms input list of dicts into dictionary to make lookups faster.
    List items identified by the type and id combination and they looks like

    {"type": item_type, "id": item_id, "attributes": {"attr1": value1, …}}

    If exclude_type is False, use pair of item "type" and "id" as a key,
    otherwise only item "id" is used.

    If simplify is True, input dictionary will be flattened, so all references
    to the resources will be replaced with the corresponding resource value.
    """
    result = dict()
    for item in data:
        key = item["id"] if exclude_type else (item["type"], item["id"])
        if key not in result:
            if not include_resources:
                result[key] = item["attributes"]
            else:
                if "relationships" in item:
                    result[key] = {
                        **item["attributes"],
                        **item["relationships"],
                    }
                else:
                    result[key] = item["attributes"]
            result[key]["id"] = item["id"]

    if simplify:
        flatten(data, result)
        result = lookup_map(data, exclude_type)

    return result


def resource(data: dict, lookup_table: dict) -> Union[dict, list[dict], None]:
    """
    Extracts resource(s) from the lookup_table.

    The data object can be a dictionary representing single resource or
    a list of dictionaries if resource can contain multiple values. Each
    resource is identified by the resource type and id.

    The lookup_table is a lookup map obtained from the JSON API response
    with the help of lookup_map(). Usually it is based on the "included"
    section of the response.
    """
    if data is None:
        return None

    result = None
    if isinstance(data, dict):
        result = lookup_table.get((data["type"], data["id"]), None)
    elif isinstance(data, list):
        attrs = list()
        for d in data:
            v = resource(d, lookup_table)
            if v is not None:
                attrs.append(v)
        result = attrs if attrs else None

    return result


def flatten(content: dict, lookup_table: dict):
    """
    Transforms JSON API response into a nested dictionary object for easier
    manipulation using passed lookup_table for resources retrieval.

    This flattens all relationships, so all references to the object's
    resources ("included" section of the response or "relationships" section
    inside the "included" object) are replaced with the corresponding values.
    """
    for item in content:
        relationships = item.pop("relationships", None)
        if relationships is None:
            continue

        for k, v in relationships.items():
            data = v.get("data", None)
            item["attributes"][k] = resource(data, lookup_table)


def attribute(
    value: Union[dict, list[dict]], key: str
) -> Union[str, list[str], None]:
    """
    Extracts value(s) identified by the given key from the value object.
    The value object can be either dictionary or list of dictionaries.
    In the latter case value will be extracted from every dictionary in list.
    """
    if value is None:
        return None

    result = None
    if isinstance(value, dict):
        result = value.get(key, None)
    elif isinstance(value, list):
        values = list()
        for i in value:
            v = attribute(i, key)
            if v is not None:
                values.append(v)
        result = values if values else None

    return result


def ows_datasource(protocol: str, data: dict, keys: list[str]):
    """
    Creates an OGC datasource class instance for the given protocol using
    information from the data dictionary. Only keys from the keys list
    will be used.
    """
    if data is None:
        return None

    # all datasources have URL
    if "url" not in keys:
        keys.append("url")

    args = dict()
    for k in keys:
        v = data.get(k, "")
        if k == "format":
            args["image_format"] = v
        elif k == "matrixSet":
            args["tile_matrix"] = v
        elif k == "typeName":
            args["typename"] = v
        else:
            args[k] = v

    if protocol == "wms":
        datasource = WmsSource(**args)
    elif protocol == "wmts":
        datasource = WmtsSource(**args)
    elif protocol == "wfs":
        datasource = WfsSource(**args)

    return datasource


def file_datasource(data: dict):
    """
    Creates file source(s) from the data dictionary.
    """
    if data is None:
        return

    files = list()
    for item in data:
        url = item.get("url", None)
        type_info = item.get("fileSourceType", None)

        file_type = None
        if type_info is not None:
            file_type = type_info.get("name", None)

        files.append(FileSource(url, file_type))

    return files


def icon(icon_file: str, url: Union[str, None]) -> QIcon:
    """
    Returns an icon from the icon_file if it is exists, otherwise tries to
    fetch icon from the given url. If url is not set or request fails
    a default icon will be returned. Fetched icon cached as a .png file.
    """
    if os.path.exists(icon_file):
        return QIcon(icon_file)

    if url is None:
        return None

    # download icon
    request = QgsBlockingNetworkRequest()
    result = request.get(QNetworkRequest(QUrl(url)))
    if result == QgsBlockingNetworkRequest.NoError:
        data = request.reply().content()
        with open(icon_file, "wb") as f:
            f.write(data)

        return QIcon(icon_file)

    return None


def collection(data: dict, lookup_map: dict) -> dict:
    """
    Returns dictionary of parameters needed to construct an instance of the
    Collection class.
    """
    params = dict()
    attrs = data["attributes"]
    params["title"] = attrs["title"]
    params["description"] = attrs["description"]

    params["datasets"] = list()
    rels = data["relationships"]
    for item in rels["datasetCollectionItems"]["data"]:
        col_item = lookup_map.get((item["type"], item["id"]), None)
        if col_item:
            params["datasets"].append(col_item["dataset"]["data"]["id"])

    return params
