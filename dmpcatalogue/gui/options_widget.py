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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QHBoxLayout

from qgis.core import QgsApplication
from qgis.gui import QgsOptionsWidgetFactory, QgsOptionsPageWidget

from dmpcatalogue.core.data_registry import DATA_REGISTRY
from dmpcatalogue.core.settings_registry import SettingsRegistry
from dmpcatalogue.constants import PLUGIN_PATH, PLUGIN_ICON

WIDGET, BASE = uic.loadUiType(
    os.path.join(PLUGIN_PATH, "ui", "options_widget.ui")
)


class DmpOptionsWidget(BASE, WIDGET):
    """
    Plugin's settings widget. Integrates into QGIS options dialog.
    """

    def __init__(self, parent):
        super(DmpOptionsWidget, self).__init__(parent)
        self.setupUi(self)

        # Ensure external links open in browser (openExternalLinks in .ui is
        # not reliably applied by PyQt5/QGIS 3.x uic)
        self.label_3.setOpenExternalLinks(True)
        self.label_4.setOpenExternalLinks(True)

        self.reloadUrl.clicked.connect(self.reload_catalog)

        self.load_options()

        self.municipalityFilterBox.currentIndexChanged.connect(
            self.on_municipality_filter_changed
        )
        self.wfsFilterGroup.toggled.connect(self.on_wfs_filter_group_toggled)

        # Sync request_bbox_checkbox enabled/checked state with the
        # wfsFilterGroup state restored in load_options().
        self.on_wfs_filter_group_toggled(self.wfsFilterGroup.isChecked())

    def load_options(self):
        self.url_line_edit.setText(SettingsRegistry.catalog_url())

        load_order = SettingsRegistry.datasource_load_order()
        for protocol in load_order:
            self.source_priority_list.addItem(protocol.upper())

        override_datafordeler = SettingsRegistry.override_datafordeler_auth()
        self.datafordeler_auth_group.setChecked(override_datafordeler)
        apikey = SettingsRegistry.datafordeler_apikey()
        self.datafordeler_apikey_edit.setText(apikey)

        override_dataforsyningen = (
            SettingsRegistry.override_dataforsyningen_auth()
        )
        self.dataforsyningen_auth_group.setChecked(override_dataforsyningen)
        token = SettingsRegistry.dataforsyningen_token()
        self.dataforsyningen_token_edit.setText(token)

        self.request_bbox_checkbox.setChecked(
            SettingsRegistry.use_request_bbox()
        )

        # Signals are blocked while populating so the restored selection
        # below does not get reported as a user change.
        self.municipalityFilterBox.blockSignals(True)
        self.municipalityFilterBox.clear()
        self.municipalityFilterBox.addItem("", None)
        municipalities = sorted(
            DATA_REGISTRY.municipalities.items(),
            key=lambda item: int(item[1]["komkode"]),
        )
        for name, attributes in municipalities:
            komkode = attributes["komkode"]
            self.municipalityFilterBox.addItem(f"{name} ({komkode})", komkode)

        saved_komkode = SettingsRegistry.municipality_filter()
        index = self.municipalityFilterBox.findData(saved_komkode)
        self.municipalityFilterBox.setCurrentIndex(max(index, 0))
        self.wfsFilterGroup.setChecked(bool(saved_komkode))
        self.municipalityFilterBox.blockSignals(False)

    def on_municipality_filter_changed(self, index):
        komkode = self.municipalityFilterBox.itemData(index) or ""
        self.wfsFilterGroup.setChecked(bool(komkode))
        SettingsRegistry.set_municipality_filter(komkode)
        DATA_REGISTRY.municipalityFilterChanged.emit(komkode)

    def on_wfs_filter_group_toggled(self, checked):
        if not checked:
            self.municipalityFilterBox.setCurrentIndex(0)

        # BBOX request restriction is redundant (and conflicting) with a
        # municipality WFS filter, so disable it while the filter is active.
        self.request_bbox_checkbox.setEnabled(not checked)
        if checked:
            self.request_bbox_checkbox.setChecked(False)

    def reload_catalog(self):
        SettingsRegistry.set_catalog_url(self.url_line_edit.text())
        DATA_REGISTRY.initialize(force_download=True)

    def accept(self):
        old_url = SettingsRegistry.catalog_url()
        SettingsRegistry.set_catalog_url(self.url_line_edit.text())
        if old_url != self.url_line_edit.text():
            DATA_REGISTRY.initialize(True)

        load_order = list()
        for i in range(self.source_priority_list.count()):
            item = self.source_priority_list.item(i)
            load_order.append(item.text().lower())

        SettingsRegistry.set_datasource_load_order(load_order)

        SettingsRegistry.set_override_datafordeler_auth(
            self.datafordeler_auth_group.isChecked()
        )
        SettingsRegistry.set_datafordeler_apikey(
            self.datafordeler_apikey_edit.text()
        )

        SettingsRegistry.set_override_dataforsyningen_auth(
            self.dataforsyningen_auth_group.isChecked()
        )
        SettingsRegistry.set_dataforsyningen_token(
            self.dataforsyningen_token_edit.text()
        )

        SettingsRegistry.set_use_request_bbox(
            self.request_bbox_checkbox.isChecked()
        )


class DmpOptionsFactory(QgsOptionsWidgetFactory):
    def __init__(self):
        super(QgsOptionsWidgetFactory, self).__init__()

    def icon(self):
        return PLUGIN_ICON

    def createWidget(self, parent):
        return DmpOptionsPage(parent)


class DmpOptionsPage(QgsOptionsPageWidget):
    def __init__(self, parent):
        super(DmpOptionsPage, self).__init__(parent)

        self.widget = DmpOptionsWidget(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setMargin(0)
        self.setLayout(layout)
        layout.addWidget(self.widget)

        self.setObjectName("dmpOptions")

    def apply(self):
        self.widget.accept()
