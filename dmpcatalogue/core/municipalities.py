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

import json
import os
from typing import Optional

from dmpcatalogue.constants import PLUGIN_PATH

# Module-level cache so the bundled JSON is only parsed once. This module has
# no dependencies on data_registry/data_classes so both can import it freely.
_municipality_geometries: Optional[dict] = None


def load_municipality_geometries() -> dict:
    """
    Loads municipality names and their simplified polygon geometries from
    the JSON file bundled with the plugin, caching the result for
    subsequent calls.
    """
    global _municipality_geometries
    if _municipality_geometries is None:
        geometries_file = os.path.join(
            PLUGIN_PATH, "data", "kommune_geometry.json"
        )
        with open(geometries_file, "r", encoding="utf-8") as f:
            _municipality_geometries = json.load(f)
    return _municipality_geometries


def municipality_geometry(komkode: str) -> Optional[list]:
    """
    Returns the polygons (a list of polygons, each a list of rings, each
    ring a list of [x, y] pairs) for the municipality with the given
    komkode, or None if not found.
    """
    for attributes in load_municipality_geometries().values():
        if attributes["komkode"] == komkode:
            return attributes["polygons"]

    return None
