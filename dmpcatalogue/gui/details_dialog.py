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

from qgis.PyQt import uic

from qgis.gui import QgsGui
from qgis.core import QgsApplication, QgsHtmlUtils

from dmpcatalogue.constants import PLUGIN_PATH
from dmpcatalogue.core.data_classes import Dataset, Collection

WIDGET, BASE = uic.loadUiType(
    os.path.join(PLUGIN_PATH, "ui", "details_dialog.ui")
)


class DetailsDialog(BASE, WIDGET):
    """
    Dialog showing detailed dataset information.
    """

    def __init__(self, item, parent=None):
        super(DetailsDialog, self).__init__(parent)
        self.setupUi(self)

        QgsGui.instance().enableAutoGeometryRestore(self)

        style = QgsApplication.reportStyleSheet()
        self.text_browser.document().setDefaultStyleSheet(style)

        if isinstance(item, Dataset):
            self.text_browser.setHtml(self.dataset_info(item))
        else:
            self.text_browser.setHtml(self.collection_info(item))

    def dataset_info(self, dataset):
        """
        Generates HTML report with the dataset information.
        """
        info = "<html><head></head>\n<body>\n"
        info += "<h1>" + self.tr("General") + "</h1>\n<hr>\n"
        info += '<table class="list-view">\n'
        info += '<tr><td class="highlight">' + self.tr("Title")
        info += "</td><td>" + dataset.title + "</td></tr>\n"
        info += '<tr><td class="highlight">' + self.tr("Category")
        info += "</td><td>" + dataset.category + "</td></tr>\n"

        if dataset.description is not None:
            info += '<tr><td class="highlight">' + self.tr("Description")
            info += "</td><td>" + dataset.description + "</td></tr>\n"

        if dataset.tags:
            info += '<tr><td class="highlight">' + self.tr("Tags")
            info += "</td><td>" + QgsHtmlUtils.buildBulletList(dataset.tags)
            info += "</td></tr>\n"

        if dataset.owners:
            info += '<tr><td class="highlight">' + self.tr("Owners")
            info += "</td><td>" + QgsHtmlUtils.buildBulletList(dataset.owners)
            info += "</td></tr>\n"

        info += "</table>\n<br><br>"

        info += "<h1>" + self.tr("Additional information") + "</h1>\n<hr>\n"
        info += '<table class="list-view">\n'
        if dataset.supportContact:
            info += '<tr><td class="highlight">' + self.tr("Support contact")
            info += (
                f"</td><td><a href='{dataset.supportContact}'>"
                + dataset.supportContact
                + "</a></td></tr>\n"
            )

        if dataset.metadata is not None:
            info += '<tr><td class="highlight">' + self.tr("Metadata")
            info += (
                f"</td><td><a href='{dataset.metadata}'>"
                + dataset.metadata
                + "</a></td></tr>\n"
            )

        info += '<tr><td class="highlight">' + self.tr("Created")
        info += f"</td><td>" + dataset.created + "</td></tr>\n"
        info += '<tr><td class="highlight">' + self.tr("Updated")
        info += f"</td><td>" + dataset.updated + "</td></tr>\n"
        info += "</table>\n<br><br>"

        if dataset.wms is not None:
            info += "<h1>" + self.tr("WMS") + "</h1>\n<hr>\n"
            info += '<table class="list-view">\n'

            info += '<tr><td class="highlight">' + self.tr("URL")
            info += f"</td><td>" + dataset.wms.url + "</td></tr>\n"
            info += '<tr><td class="highlight">' + self.tr("Layer")
            info += f"</td><td>" + dataset.wms.layer + "</td></tr>\n"
            if dataset.wms.style is not None:
                info += '<tr><td class="highlight">' + self.tr("Style")
                info += f"</td><td>" + dataset.wms.style + "</td></tr>\n"
            info += '<tr><td class="highlight">' + self.tr("Format")
            info += f"</td><td>" + dataset.wms.image_format + "</td></tr>\n"

            info += "</table>\n<br><br>"

        if dataset.wfs is not None:
            info += "<h1>" + self.tr("WFS") + "</h1>\n<hr>\n"
            info += '<table class="list-view">\n'

            info += '<tr><td class="highlight">' + self.tr("URL")
            info += f"</td><td>" + dataset.wfs.url + "</td></tr>\n"
            info += '<tr><td class="highlight">' + self.tr("Type name")
            info += f"</td><td>" + dataset.wfs.typename + "</td></tr>\n"

            info += "</table>\n<br><br>"

        if dataset.wmts is not None:
            info += "<h1>" + self.tr("WMTS") + "</h1>\n<hr>\n"
            info += '<table class="list-view">\n'

            info += '<tr><td class="highlight">' + self.tr("URL")
            info += f"</td><td>" + dataset.wmts.url + "</td></tr>\n"
            info += '<tr><td class="highlight">' + self.tr("Layer")
            info += f"</td><td>" + dataset.wmts.layer + "</td></tr>\n"
            if dataset.wmts.style is not None:
                info += '<tr><td class="highlight">' + self.tr("Style")
                info += f"</td><td>" + dataset.wmts.style + "</td></tr>\n"
            info += '<tr><td class="highlight">' + self.tr("Tile matrix")
            info += f"</td><td>" + dataset.wmts.tile_matrix + "</td></tr>\n"
            info += '<tr><td class="highlight">' + self.tr("Format")
            info += f"</td><td>" + dataset.wmts.image_format + "</td></tr>\n"

            info += "</table>\n<br><br>"

        return info

    def collection_info(self, collection):
        """
        Generates HTML report with the collection information.
        """
        info = "<html><head></head>\n<body>\n"
        info += "<h1>" + self.tr("General") + "</h1>\n<hr>\n"
        info += '<table class="list-view">\n'
        info += '<tr><td class="highlight">' + self.tr("Title")
        info += "</td><td>" + collection.title + "</td></tr>\n"

        if collection.description is not None:
            info += '<tr><td class="highlight">' + self.tr("Description")
            info += "</td><td>" + collection.description + "</td></tr>\n"
        info += "</table>\n<br><br>"

        return info
