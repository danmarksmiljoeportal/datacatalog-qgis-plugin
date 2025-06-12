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

from qgis.PyQt.QtCore import QModelIndex, QItemSelectionModel
from qgis.PyQt.QtWidgets import QTreeView

from dmpcatalogue.core.data_classes import Dataset
from dmpcatalogue.gui.dataset_item_model import (
    DatasetProxyModel,
    DatasetItemModel,
)


class DatasetTreeView(QTreeView):
    """
    Dataset tree view, showing datasets in a tree structure.
    """

    def __init__(self, parent=None, registry=None):
        super(DatasetTreeView, self).__init__(parent)

        self.proxy_model = DatasetProxyModel(self, registry)
        self.datasets_model = self.proxy_model.datasets_model()
        self.setModel(self.proxy_model)

    def set_filter_string(self, filter_string: str):
        """
        Sets a filter string, used to filter out the contents of the view
        to matching algorithms.
        """
        text = filter_string.strip().lower()
        self.proxy_model.set_filter_string(text)

        if text != "":
            self.expandAll()

            # if previously selected item was hidden, auto select the first
            # visible dataset
            if self.selected_dataset() is None:
                first_visible_index = self.find_first_visible_dataset(
                    QModelIndex()
                )
                if first_visible_index.isValid():
                    self.selectionModel().setCurrentIndex(
                        first_visible_index,
                        QItemSelectionModel.SelectionFlag.Clear
                        | QItemSelectionModel.SelectionFlag.Select,
                    )
        else:
            self.collapseAll()

    def set_filters(self, filters):
        """
        Sets filters controlling the view's contents.
        """
        self.proxy_model.set_filters(filters)

    def dataset_for_index(self, index: QModelIndex) -> Union[Dataset, None]:
        """
        Returns the dataset at the specified tree view index, or None
        if the index does not correspond to a dataset.
        """
        source_index = self.proxy_model.mapToSource(index)
        if self.datasets_model.is_dataset(source_index):
            return self.datasets_model.dataset_for_index(source_index)
        else:
            return None

    def selected_dataset(self) -> Union[Dataset, None]:
        """
        Returns the currently selected dataset in the tree view, or None
        if no dataset is currently selected.
        """
        if self.selectionModel().hasSelection():
            index = self.selectionModel().selectedIndexes()[0]
            return self.dataset_for_index(index)
        else:
            return None

    def dataset_group_for_index(
        self, index: QModelIndex
    ) -> Union[list[Dataset], None]:
        """
        Returns a dataset group at the specified tree view index, or None
        if the index does not correspond to a dataset group.
        """
        source_index = self.proxy_model.mapToSource(index)
        if self.datasets_model.is_category(source_index):
            return self.datasets_model.dataset_group_for_index(source_index)
        else:
            return None

    def selected_dataset_group(self) -> Union[list[Dataset], None]:
        """
        Returns the currently selected dataset group in the tree view, or None
        if no dataset group is currently selected.
        """
        if self.selectionModel().hasSelection():
            index = self.selectionModel().selectedIndexes()[0]
            return self.dataset_group_for_index(index)
        else:
            return None

    def collection_for_index(
        self, index: QModelIndex
    ) -> Union[Collection, None]:
        """
        Returns a collection at the specified tree view index, or None
        if the index does not correspond to a collection.
        """
        source_index = self.proxy_model.mapToSource(index)
        if self.datasets_model.is_collection(source_index):
            return self.datasets_model.collection_for_index(source_index)
        else:
            return None

    def selected_collection(self) -> Union[Collection, None]:
        """
        Returns the currently selected collection in the tree view, or None
        if no collection is currently selected.
        """
        if self.selectionModel().hasSelection():
            index = self.selectionModel().selectedIndexes()[0]
            return self.collection_for_index(index)
        else:
            return None

    def find_first_visible_dataset(self, parent: QModelIndex) -> QModelIndex:
        """
        Returns the first visible dataset in the tree.
        """
        for r in range(self.proxy_model.rowCount(parent)):
            proxy_index = self.proxy_model.index(r, 0, parent)
            source_index = self.proxy_model.mapToSource(proxy_index)
            if self.datasets_model.is_dataset(source_index):
                return proxy_index

            index = self.find_first_visible_dataset(proxy_index)
            if index.isValid():
                return index

        return QModelIndex()
