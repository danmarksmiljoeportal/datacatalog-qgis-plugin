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

        self.load_options()

    def load_options(self):
        self.url_line_edit.setText(SettingsRegistry.catalog_url())

        load_order = SettingsRegistry.datasource_load_order()
        for protocol in load_order:
            self.source_priority_list.addItem(protocol.upper())

        override_datafordeler = SettingsRegistry.override_datafordeler_auth()
        self.datafordeler_auth_group.setChecked(override_datafordeler)
        login, password = SettingsRegistry.datafordeler_auth()
        self.datafordeler_login_edit.setText(login)
        self.datafordeler_password_edit.setText(password)

        override_dataforsyningen = (
            SettingsRegistry.override_dataforsyningen_auth()
        )
        self.dataforsyningen_auth_group.setChecked(override_dataforsyningen)
        token = SettingsRegistry.dataforsyningen_token()
        self.dataforsyningen_token_edit.setText(token)

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
        SettingsRegistry.set_datafordeler_auth(
            self.datafordeler_login_edit.text(),
            self.datafordeler_password_edit.text(),
        )

        SettingsRegistry.set_override_dataforsyningen_auth(
            self.dataforsyningen_auth_group.isChecked()
        )
        SettingsRegistry.set_dataforsyningen_token(
            self.dataforsyningen_token_edit.text()
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
