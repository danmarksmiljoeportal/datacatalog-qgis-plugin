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

import os
import json

from qgis.PyQt.QtCore import pyqtSignal

from qgis.core import QgsTask

from dmpcatalogue.core.data_classes import Dataset, Collection
from dmpcatalogue.core.utils import (
    cache_directory,
    lookup_map,
    flatten,
    attribute,
    ows_datasource,
    file_datasource,
    icon,
    collection,
)
from dmpcatalogue.constants import PLUGIN_ICON


class DataParserTask(QgsTask):
    """
    Loads datasets from the cached server reply. Emits processed signal
    when finished. Loaded datasets can be accessed via datasets class member.
    """

    processed = pyqtSignal()

    def __init__(self):
        QgsTask.__init__(self)

        self.datasets = dict()
        self.collections = dict()

    def run(self):
        cache_root = cache_directory()

        icon_cache = os.path.join(cache_root, "thumbnails")
        os.makedirs(icon_cache, exist_ok=True)

        # read and parse datasets status info
        status_info = dict()
        cache_file = os.path.join(cache_root, "status.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                content = json.load(f)

            # reply contains only status information, it is enough to have
            # only uid as a key
            status_info = lookup_map(content["data"], True)

        # read and parse datatsets metadata
        cache_file = os.path.join(cache_root, "datasets.json")
        with open(cache_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        meta = content.get("meta", None)
        if meta is None:
            return False

        if meta["total"] == 0:
            return False

        lookup_table = lookup_map(content["included"], simplify=True)

        flatten(content["data"], lookup_table)
        step = 90 / len(content["data"])
        for i, item in enumerate(content["data"]):
            if self.isCanceled():
                return False

            uid = item["id"]
            attributes = item["attributes"]

            # create datasources
            for dtype, keys in (
                ("wfsSource", ["typeName"]),
                ("wmsSource", ["layer", "style", "format"]),
                ("wmtsSource", ["layer", "style", "format", "matrixSet"]),
            ):
                data = attributes.pop(dtype, None)
                protocol = dtype[:-6].lower()
                attributes[protocol] = ows_datasource(protocol, data, keys)

            # process fileSources attribute
            data = attributes.pop("fileSources", None)
            attributes["files"] = file_datasource(data)

            data = attributes.pop("thumbnail", None)
            attributes["thumbnail"] = attribute(data, "url")

            data = attributes.pop("category", None)
            attributes["category"] = attribute(data, "name")
            attributes["category_icon"] = PLUGIN_ICON

            if attributes["thumbnail"] is None:
                t = data.pop("thumbnail", None)
                attributes["thumbnail"] = attribute(t, "url")

            # extract necessary information from the complex attributes
            for key, field in (
                ("tags", "name"),
                ("owners", "title"),
            ):
                data = attributes.pop(key, None)
                attributes[key] = attribute(data, field)

            # inject status info
            status = attribute(status_info.get(uid, None), "status")
            attributes["status"] = status

            # dataset icon
            safe_uid = str(uid)
            for c in (".", ":"):
                if c in safe_uid:
                    safe_uid = safe_uid.replace(c, "-")
            icon_file = os.path.join(icon_cache, safe_uid)
            url = attributes.get("thumbnail", None)
            attributes["thumbnail"] = icon(icon_file, url)

            ds = Dataset(uid, **attributes)
            self.datasets[uid] = ds

            self.setProgress(i * step)

        # read and parse collections metadata
        cache_file = os.path.join(cache_root, "collections.json")
        with open(cache_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        lookup_table = lookup_map(content["included"], include_resources=True)
        step = 10 / len(content["data"])
        for i, item in enumerate(content["data"]):
            if self.isCanceled():
                return False

            uid = item["id"]
            attributes = collection(item, lookup_table)
            self.collections[uid] = Collection(uid, **attributes)

            self.setProgress(self.progress() + i * step)

        self.processed.emit()
        return True
