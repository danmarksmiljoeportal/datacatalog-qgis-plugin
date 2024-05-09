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

from qgis.PyQt.QtCore import Qt, QCoreApplication, QTranslator, QUrl
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QDesktopServices

from qgis.core import QgsApplication, Qgis

from dmpcatalogue.core.data_registry import DATA_REGISTRY
from dmpcatalogue.gui.dock_widget import CatalogueDockWidget
from dmpcatalogue.gui.options_widget import DmpOptionsFactory
from dmpcatalogue.constants import PLUGIN_PATH, PLUGIN_ICON


class DmpPlugin:
    def __init__(self, iface):
        self.iface = iface

        locale = QgsApplication.locale()
        qm_path = "{}/i18n/dmpcatalogue_{}.qm".format(PLUGIN_PATH, locale)

        if os.path.exists(qm_path):
            self.translator = QTranslator()
            self.translator.load(qm_path)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.options_factory = DmpOptionsFactory()
        self.options_factory.setTitle(self.tr("DMP Catalogue"))
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        self.dock_widget = CatalogueDockWidget()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.hide()
        self.dock_widget.visibilityChanged.connect(self.toggle_dock_action)

        self.dock_action = QAction(
            self.tr("DMP Catalogue"), self.iface.mainWindow()
        )
        self.dock_action.setIcon(PLUGIN_ICON)
        self.dock_action.setObjectName("toggleDmpCatalogue")
        self.dock_action.setCheckable(True)
        self.dock_action.toggled.connect(self.toggle_dock_widget)

        self.settings_action = QAction(
            self.tr("Settings"), self.iface.mainWindow()
        )
        self.settings_action.setIcon(
            QgsApplication.getThemeIcon("/mActionOptions.svg")
        )
        self.settings_action.setObjectName("dmpCatalogueSettings")
        self.settings_action.triggered.connect(self.open_settings)

        self.help_action = QAction(self.tr("Help"), self.iface.mainWindow())
        self.help_action.setIcon(
            QgsApplication.getThemeIcon("/mActionHelpContents.svg")
        )
        self.help_action.setObjectName("dmpCatalogueHelp")
        self.help_action.triggered.connect(self.open_help)

        self.iface.addPluginToWebMenu(
            self.tr("DMP Catalogue"), self.dock_action
        )
        self.iface.addPluginToWebMenu(
            self.tr("DMP Catalogue"), self.settings_action
        )
        self.iface.addPluginToWebMenu(
            self.tr("DMP Catalogue"), self.help_action
        )
        self.iface.addWebToolBarIcon(self.dock_action)

        DATA_REGISTRY.initialize()
        DATA_REGISTRY.requestFailed.connect(self.report_error)

    def unload(self):
        self.iface.removePluginWebMenu(
            self.tr("DMP Catalogue"), self.dock_action
        )
        self.iface.removePluginWebMenu(
            self.tr("DMP Catalogue"), self.settings_action
        )
        self.iface.removePluginWebMenu(
            self.tr("DMP Catalogue"), self.help_action
        )
        self.iface.removeWebToolBarIcon(self.dock_action)

        self.dock_widget.setUserVisible(False)
        self.iface.removeDockWidget(self.dock_widget)

        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

    def toggle_dock_action(self, visible):
        self.dock_action.setChecked(visible)

    def toggle_dock_widget(self, checked):
        self.dock_widget.setUserVisible(checked)

    def open_help(self):
        QDesktopServices.openUrl(
            QUrl(
                "https://github.com/strandbygaard/DmpQgisDataCatalogue/"
                "blob/master/README.md"
            )
        )

    def open_settings(self):
        self.iface.showOptionsDialog(self.iface.mainWindow(), "dmpOptions")

    def report_error(self, message):
        self.iface.messageBar().pushMessage(
            self.tr("DMP Catalogue"), message, Qgis.Warning
        )

    def tr(self, text):
        return QCoreApplication.translate(self.__class__.__name__, text)
