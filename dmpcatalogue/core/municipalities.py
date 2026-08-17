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
_municipalities: Optional[dict] = None


def load_municipalities() -> dict:
    """
    Loads municipality names and their BBOXes from the JSON file bundled
    with the plugin, caching the result for subsequent calls.
    """
    global _municipalities
    if _municipalities is None:
        municipalities_file = os.path.join(
            PLUGIN_PATH, "data", "kommune_bbox.json"
        )
        with open(municipalities_file, "r", encoding="utf-8") as f:
            _municipalities = json.load(f)
    return _municipalities


def municipality_bbox(komkode: str) -> Optional[dict]:
    """
    Returns the BBOX attributes (xmin, xmax, ymin, ymax, komkode) for the
    municipality with the given komkode, or None if not found.
    """
    for attributes in load_municipalities().values():
        if attributes["komkode"] == komkode:
            return attributes

    return None
