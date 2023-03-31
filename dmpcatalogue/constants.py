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

from qgis.PyQt.QtGui import QIcon


PLUGIN_PATH = os.path.dirname(__file__)
PLUGIN_ICON = QIcon(os.path.join(PLUGIN_PATH, "icons", "dmpcatalogue.svg"))

# defaults for settings
DEFAULT_API_ROOT = "https://datakatalog.miljoeportal.dk/api"
DEFAULT_LOAD_ORDER = ["wfs", "wmts", "wms"]
