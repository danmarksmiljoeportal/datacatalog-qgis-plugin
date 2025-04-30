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
from functools import partial

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtWidgets import QMenu, QFileDialog, QActionGroup, QToolButton

from qgis.gui import QgsDockWidget
from qgis.core import Qgis, QgsProject, QgsApplication
from qgis.utils import iface

from dmpcatalogue.core.settings_registry import SettingsRegistry
from dmpcatalogue.core.data_registry import DATA_REGISTRY
from dmpcatalogue.gui.dataset_item_model import Filters, Mode
from dmpcatalogue.gui.details_dialog import DetailsDialog
from dmpcatalogue.constants import PLUGIN_PATH


WIDGET, BASE = uic.loadUiType(
    os.path.join(PLUGIN_PATH, "ui", "catalogue_widget.ui")
)


class CatalogueDockWidget(QgsDockWidget, WIDGET):
    """
    DMP Catalogue dock widget, used for browsing and loading dataset.
    """

    def __init__(self, parent=None):
        super(CatalogueDockWidget, self).__init__(parent)
        self.setupUi(self)

        self.dataset_toolbar.setIconSize(iface.iconSize(True))
        self.collection_toolbar.setIconSize(iface.iconSize(True))

        ds_menu = QMenu()
        all_ds_action = ds_menu.addAction(self.tr("All"))
        all_ds_action.setCheckable(True)
        all_ds_action.triggered.connect(
            lambda: self.set_dataset_filters(Filters.ShowAll)
        )

        ows_ds_action = ds_menu.addAction(self.tr("OWS"))
        ows_ds_action.setCheckable(True)
        ows_ds_action.setChecked(True)
        ows_ds_action.triggered.connect(
            lambda: self.set_dataset_filters(Filters.ShowOws)
        )
        self.set_dataset_filters(Filters.ShowOws)

        file_ds_action = ds_menu.addAction(self.tr("File"))
        file_ds_action.setCheckable(True)
        file_ds_action.triggered.connect(
            lambda: self.set_dataset_filters(Filters.ShowFiles)
        )

        ds_group = QActionGroup(ds_menu)
        ds_group.addAction(all_ds_action)
        ds_group.addAction(ows_ds_action)
        ds_group.addAction(file_ds_action)
        self.datasources_source_action.setMenu(ds_menu)
        self.dataset_toolbar.widgetForAction(
            self.datasources_source_action
        ).setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.datasources_source_action.setIcon(
            QIcon(os.path.join(PLUGIN_PATH, "icons", "datasources.svg"))
        )
        self.group_owners_action.setIcon(
            QIcon(os.path.join(PLUGIN_PATH, "icons", "group.svg"))
        )
        self.group_owners_action.toggled.connect(self.toggle_group_owners)

        self.options_action.setIcon(
            QgsApplication.getThemeIcon("/mActionOptions.svg")
        )
        self.options_action.triggered.connect(self.open_plugin_options)

        col_menu = QMenu()
        all_col_action = col_menu.addAction(self.tr("All"))
        all_col_action.setCheckable(True)
        all_col_action.triggered.connect(
            lambda: self.set_collection_filters(Filters.ShowAll)
        )

        ows_col_action = col_menu.addAction(self.tr("OWS"))
        ows_col_action.setCheckable(True)
        ows_col_action.setChecked(True)
        ows_col_action.triggered.connect(
            lambda: self.set_collection_filters(Filters.ShowOws)
        )

        file_col_action = col_menu.addAction(self.tr("File"))
        file_col_action.setCheckable(True)
        file_col_action.triggered.connect(
            lambda: self.set_collection_filters(Filters.ShowFiles)
        )

        col_group = QActionGroup(col_menu)
        col_group.addAction(all_col_action)
        col_group.addAction(ows_col_action)
        col_group.addAction(file_col_action)
        self.collections_source_action.setMenu(col_menu)
        self.collection_toolbar.widgetForAction(
            self.collections_source_action
        ).setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.collections_source_action.setIcon(
            QIcon(os.path.join(PLUGIN_PATH, "icons", "datasources.svg"))
        )

        self.search_dataset.setShowSearchIcon(True)
        self.search_collection.setShowSearchIcon(True)

        self.dataset_tree.set_filters(Filters.ShowAll)
        self.collection_tree.set_filters(Filters.ShowAll)
        self.collection_tree.datasets_model.set_show_collections(True)

        self.collection_tree.doubleClicked.connect(self.handle_doubleclick)

        self.registry = DATA_REGISTRY

        self.registry.fileDownloaded.connect(
            lambda file_name: self.show_message(
                self.tr(f"File downloaded ")
                + f"<a href='{QUrl.fromLocalFile(file_name).toString()}'>"
                + f"{file_name}</a>.",
                Qgis.Info,
            )
        )
        self.registry.downloadFailed.connect(self.show_message)

        self.search_dataset.textChanged.connect(self.set_dataset_filter_string)
        self.dataset_tree.customContextMenuRequested.connect(
            self.dataset_context_menu
        )
        self.dataset_tree.doubleClicked.connect(lambda: self.add_dataset())

        self.search_collection.textChanged.connect(
            self.set_collection_filter_string
        )
        self.collection_tree.customContextMenuRequested.connect(
            self.collection_context_menu
        )

    def set_dataset_filter_string(self, filter_string):
        self.dataset_tree.set_filter_string(filter_string)

    def set_dataset_filters(self, filters):
        self.dataset_tree.set_filters(filters)

    def set_collection_filter_string(self, filter_string):
        self.collection_tree.set_filter_string(filter_string)

    def set_collection_filters(self, filters):
        self.collection_tree.set_filters(filters)

    def dataset_context_menu(self, point):
        index = self.dataset_tree.indexAt(point)
        menu = QMenu()
        dataset = self.dataset_tree.dataset_for_index(index)
        if dataset is not None:
            if dataset.has_ows_source():
                ows_menu = menu.addMenu(self.tr("Add"))
                menu.addSeparator()
                for protocol in ("wfs", "wms", "wmts"):
                    source = getattr(dataset, protocol)
                    if source is not None:
                        action = ows_menu.addAction(
                            self.tr(f"{protocol.upper()} layer")
                        )
                        handler = partial(self.add_dataset, protocol)
                        action.triggered.connect(handler)

            if dataset.has_files():
                files_menu = menu.addMenu(self.tr("Download"))
                menu.addSeparator()
                for f in dataset.files:
                    action = files_menu.addAction(f.file_type)
                    action.triggered.connect(lambda: self.download_file(f.url))

            text = (
                self.tr("Remove from Favorite")
                if dataset.uid in self.registry.favorites
                else self.tr("Add to Favorite")
            )
            favorite_action = menu.addAction(text)
            favorite_action.triggered.connect(self.toggle_favorite_state)

            details_action = menu.addAction(self.tr("Details…"))
            details_action.triggered.connect(
                lambda: self.show_dataset_details(dataset)
            )
            try:
                menu.exec_(self.dataset_tree.mapToGlobal(point))
            except AttributeError:
                menu.exec(self.dataset_tree.mapToGlobal(point))

    def collection_context_menu(self, point):
        index = self.collection_tree.indexAt(point)
        menu = QMenu()

        collection = self.collection_tree.collection_for_index(index)
        if collection is not None:
            col_add_action = menu.addAction(self.tr("Add"))
            col_add_action.triggered.connect(self.add_collection)

            col_details_action = menu.addAction(self.tr("Details…"))
            col_details_action.triggered.connect(
                lambda: self.show_collection_details(collection)
            )

        if collection is None:
            collection = (
                self.collection_tree.datasets_model.collection_for_index(
                    self.collection_tree.datasets_model.parent(
                        self.collection_tree.proxy_model.mapToSource(index)
                    )
                )
            )

        dataset = self.collection_tree.dataset_for_index(index)
        if dataset is not None:
            if dataset.has_ows_source():
                ows_menu = menu.addMenu(self.tr("Add"))
                menu.addSeparator()
                for protocol in ("wfs", "wms", "wmts"):
                    source = getattr(dataset, protocol)
                    if source is not None:
                        action = ows_menu.addAction(
                            self.tr(f"{protocol.upper()} layer")
                        )
                        handler = partial(
                            self.add_dataset_collection,
                            collection,
                            dataset,
                            protocol,
                        )
                        action.triggered.connect(handler)

            if dataset.has_files():
                files_menu = menu.addMenu(self.tr("Download"))
                menu.addSeparator()
                for f in dataset.files:
                    action = files_menu.addAction(f.file_type)
                    action.triggered.connect(lambda: self.download_file(f.url))

            ds_details_action = menu.addAction(self.tr("Details…"))
            ds_details_action.triggered.connect(
                lambda: self.show_dataset_details(dataset)
            )

        try:
            menu.exec_(self.collection_tree.mapToGlobal(point))
        except AttributeError:
            menu.exec(self.collection_tree.mapToGlobal(point))

    def add_dataset(self, protocol=""):
        dataset = self.dataset_tree.selected_dataset()
        if dataset is not None:
            layer = dataset.layer(protocol)

            if layer is None:
                self.show_message(self.tr("Dataset has no layers."))
                return

            if not layer.isValid():
                self.show_message(
                    self.tr("Failed to load layer: ") + layer.error().message(),
                )
                return

            QgsProject.instance().addMapLayer(layer, False)
            r = QgsProject.instance().layerTreeRoot()
            r.insertLayer(0, layer)

    def add_collection(self):
        collection = self.collection_tree.selected_collection()
        if collection is not None:
            root = QgsProject.instance().layerTreeRoot()
            group = root.findGroup(collection.title)
            if group is None:
                group = root.addGroup(collection.title)
            else:
                root.removeChildNode(group)
                group = root.addGroup(collection.title)

            errors = list()
            for ds in collection.datasets:
                if ds in self.registry.datasets:
                    d = self.registry.datasets[ds]
                    layer = d.layer()
                    if layer is None:
                        errors.append(
                            self.tr("There are no layers in the dataset ")
                            + d.title
                        )
                        continue
                    if not layer.isValid():
                        errors.append(
                            self.tr("Failed to load ")
                            + d.title
                            + ": "
                            + layer.error().message()
                        )
                        continue
                    QgsProject.instance().addMapLayer(layer, False)
                    group.addLayer(layer)

            if errors:
                self.show_message("\n".join(errors))

    def handle_doubleclick(self, index):
        collection = self.collection_tree.collection_for_index(index)
        if collection is None:
            return

        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(collection.title)
        if group is None:
            group = root.insertGroup(0, collection.title)
        else:
            root.removeChildNode(group)
            group = root.insertGroup(0, collection.title)

        errors = list()
        for ds in collection.datasets:
            if ds in self.registry.datasets:
                d = self.registry.datasets[ds]
                layer = d.layer()
                if layer is None:
                    errors.append(
                        self.tr("There are no layers in the dataset ") + d.title
                    )
                    continue
                if not layer.isValid():
                    errors.append(
                        self.tr("Failed to load ")
                        + d.title
                        + ": "
                        + layer.error().message()
                    )
                    continue
                QgsProject.instance().addMapLayer(layer, False)
                group.addLayer(layer)

        if errors:
            self.show_message("\n".join(errors))

    def add_dataset_collection(self, collection, dataset, protocol=""):
        if collection is not None and dataset is not None:
            root = QgsProject.instance().layerTreeRoot()
            group = root.findGroup(collection.title)
            if group is None:
                group = root.addGroup(collection.title)

            layer = dataset.layer(protocol)
            if layer is None:
                self.show_message(self.tr("Dataset has no layers."))
                return

            if not layer.isValid():
                self.show_message(
                    self.tr("Failed to load layer: ") + layer.error().message(),
                )
                return

            QgsProject.instance().addMapLayer(layer, False)
            group.addLayer(layer)

    def download_file(self, url):
        last_used_directory = SettingsRegistry.last_used_directory()
        file_name, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Save File"),
            last_used_directory,
            self.tr("ZIP Archives (*.zip *.ZIP)"),
        )
        if file_name:
            SettingsRegistry.set_last_used_directory(os.path.dirname(file_name))
            self.registry.download_file(url, file_name)

    def toggle_favorite_state(self):
        dataset = self.dataset_tree.selected_dataset()
        if dataset is not None:
            self.registry.add_or_remove_favorite(dataset.uid)

    def show_dataset_details(self, dataset):
        if dataset is not None:
            dlg = DetailsDialog(dataset)
            try:
                dlg.exec_()
            except AttributeError:
                dlg.exec()

    def show_collection_details(self, collection):
        if collection is not None:
            dlg = DetailsDialog(collection)
            try:
                dlg.exec_()
            except AttributeError:
                dlg.exec()

    def toggle_group_owners(self, checked):
        if checked:
            self.dataset_tree.datasets_model.set_mode(Mode.GroupOwners)
        else:
            self.dataset_tree.datasets_model.set_mode(Mode.GroupCategories)

    def open_plugin_options(self):
        iface.showOptionsDialog(iface.mainWindow(), "dmpOptions")

    def show_message(self, message, level=Qgis.Warning):
        iface.messageBar().pushMessage(self.tr("DMP Catalogue"), message, level)
