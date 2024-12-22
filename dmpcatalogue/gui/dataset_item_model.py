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

from typing import Union, Type, Any
from enum import Enum, IntEnum, auto
from locale import strcoll

from qgis.PyQt.QtGui import QColor, QBrush
from qgis.PyQt.QtCore import (
    pyqtSignal,
    Qt,
    QAbstractItemModel,
    QModelIndex,
    QSortFilterProxyModel,
)

from qgis.core import QgsApplication

from dmpcatalogue.core.data_registry import DATA_REGISTRY
from dmpcatalogue.constants import PLUGIN_ICON


class NodeType(Enum):
    """
    Enumeration of possible model node types.
    """

    NodeCategory = auto()
    NodeDataset = auto()
    NodeFavorite = auto()
    NodeCollection = auto()
    NodeOwner = auto()


class Roles(IntEnum):
    """
    Custom roles used by the dataset model.
    """

    RoleNodeType = Qt.ItemDataRole.UserRole
    RoleDatasetUid = auto()
    RoleDatasetTitle = auto()
    RoleDatasetDescription = auto()
    RoleDatasetTags = auto()


class Filters(Enum):
    """
    Available filters for filtering the model.
    """

    ShowAll = auto()
    ShowOws = auto()
    ShowFiles = auto()


class Mode(Enum):
    """
    Enumeration of possible model operation modes.
    """

    GroupCategories = auto()
    GroupOwners = auto()


class ModelNode:
    """
    Base class for nodes contained within DatasetItemModel.
    """

    def __init__(self):
        self.parent = None
        self.children = list()
        self.node_type = NodeType.NodeCategory

    def get_child_category_node(
        self, category: str
    ) -> Union[Type[ModelNode], None]:
        """
        Tries to find a child node belonging to this node, which corresponds
        to a category node with the given category name. Returns None if no
        matching child category node was found.
        """
        for node in self.children:
            if node.node_type == NodeType.NodeCategory:
                if node.category == category:
                    return node
        return None

    def add_child_node(self, node: Type[ModelNode]):
        """
        Adds a child node to this node.
        """
        if node is None:
            return

        node.parent = self
        self.children.append(node)

    def delete_children(self):
        """
        Deletes all child nodes from this node.
        """
        self.children.clear()


class FavoriteNode(ModelNode):
    """
    Model node corresponding to the favorite datasets group.
    """

    def __init__(self):
        super(FavoriteNode, self).__init__()
        self.node_type = NodeType.NodeFavorite


class CategoryNode(ModelNode):
    """
    Model node corresponding to a category of datasets.
    """

    def __init__(self, category, icon=None):
        super(CategoryNode, self).__init__()
        self.category = category
        self.icon = icon


class OwnerNode(ModelNode):
    """
    Model node corresponding to a owner of datasets.
    """

    def __init__(self, owner):
        super(OwnerNode, self).__init__()
        self.node_type = NodeType.NodeOwner
        self.owner = owner


class CollectionNode(ModelNode):
    """
    Model node corresponding to a collection of datasets.
    """

    def __init__(self, collection):
        super(CollectionNode, self).__init__()
        self.node_type = NodeType.NodeCollection
        self.collection = collection
        self.title = collection.title
        self.icon = collection.icon


class DatasetNode(ModelNode):
    """
    Model node corresponding to a dataset.
    """

    def __init__(self, dataset):
        super(DatasetNode, self).__init__()
        self.node_type = NodeType.NodeDataset
        self.dataset = dataset


class DatasetItemModel(QAbstractItemModel):
    """
    A model for datasets shown within the DMP Catalogue widget.
    """

    favoriteAdded = pyqtSignal()

    def __init__(self, parent=None, registry=None):
        super(DatasetItemModel, self).__init__(parent)

        self.registry = DATA_REGISTRY if registry is None else registry
        self.root_node = CategoryNode("")
        self.favorite_node = None
        self.show_collections = False
        self.mode = Mode.GroupCategories

        self.rebuild()

        self.registry.initialized.connect(self.rebuild)
        self.registry.favoritesChanged.connect(self.repopulate_favorites)

    def set_show_collections(self, show_collections):
        self.show_collections = show_collections
        self.rebuild()

    def rebuild(self):
        """
        Rebuilds model. This resets model state and repopulates it from
        the data registry.
        """
        self.beginResetModel()

        self.root_node.delete_children()
        if self.mode == Mode.GroupCategories:
            self.root_node = CategoryNode("")
        else:
            self.root_node = OwnerNode("")

        if self.registry:
            self.favorite_node = FavoriteNode()
            self.root_node.add_child_node(self.favorite_node)
            self.repopulate_favorites(True)

            if self.show_collections:
                for col in self.registry.collections.values():
                    self.add_collection(col)
            else:
                for ds in self.registry.datasets.values():
                    self.add_dataset(ds)

        self.endResetModel()

    def set_mode(self, mode):
        self.mode = mode
        self.rebuild()

    def repopulate_favorites(self, resetting=False):
        """
        Repopulates Favorites top-level node using infomation from the data
        registry.
        """
        if self.favorite_node is None:
            return

        recent_index = self.index(0, 0)
        prev_count = self.rowCount(recent_index)

        if not resetting and prev_count > 0:
            self.beginRemoveRows(recent_index, 0, prev_count - 1)
            self.favorite_node.delete_children()
            self.endRemoveRows()

        if len(self.registry.favorites) == 0:
            if not resetting:
                self.favoriteAdded.emit()
            return

        datasets = list()
        for uid in self.registry.favorites:
            dataset = self.registry.datasets.get(uid, None)
            if dataset is not None:
                datasets.append(dataset)

        if len(datasets) == 0:
            if not resetting:
                self.favoriteAdded.emit()
            return

        if not resetting:
            self.beginInsertRows(recent_index, 0, len(datasets) - 1)

        for ds in datasets:
            dataset_node = DatasetNode(ds)
            self.favorite_node.add_child_node(dataset_node)

        if not resetting:
            self.endInsertRows()
            self.favoriteAdded.emit()

    def index2node(self, index: QModelIndex) -> Type[ModelNode]:
        """
        Returns the model node corresponding to the given index.
        """
        if not index.isValid():
            return self.root_node

        return index.internalPointer()

    def node2index(self, node: Type[ModelNode]) -> QModelIndex:
        """
        Returns the model index corresponding to the given node.
        """
        if node is None or node.parent is None:
            return QModelIndex()

        parent_index = self.node2index(node.parent)
        row = node.parent.children.index(node)
        return self.index(row, 0, parent_index)

    def add_dataset(self, dataset: Dataset):
        """
        Creates a node for a dataset and adds it to the model.
        """
        parent_node = self.root_node

        if self.mode == Mode.GroupCategories:
            dataset_node = DatasetNode(dataset)
            category = dataset.category
            if category != "":
                category_node = parent_node.get_child_category_node(category)
                if category_node is None:
                    category_node = CategoryNode(
                        category, dataset.category_icon
                    )
                    parent_node.add_child_node(category_node)
                category_node.add_child_node(dataset_node)
            else:
                parent_node.add_child_node(dataset_node)
        elif self.mode == Mode.GroupOwners:
            for owner in dataset.owners:
                dataset_node = DatasetNode(dataset)
                if owner != "":
                    owner_node = parent_node.get_child_category_node(owner)
                    if owner_node is None:
                        owner_node = CategoryNode(owner)
                        parent_node.add_child_node(owner_node)
                    owner_node.add_child_node(dataset_node)
                else:
                    parent_node.add_child_node(dataset_node)

    def add_collection(self, collection: Collection):
        """
        Creates a node for a collection and adds it to the model.
        """
        parent_node = self.root_node

        collection_node = CollectionNode(collection)
        for ds in collection.datasets:
            if ds in self.registry.datasets:
                dataset_node = DatasetNode(self.registry.datasets[ds])
                collection_node.add_child_node(dataset_node)
        parent_node.add_child_node(collection_node)

    def tooltip_for_dataset(self, dataset: Dataset) -> str:
        """
        Returns a formatted tooltip for a dataset.
        """
        text = f"<p><b>{dataset.title}</b></p>"

        description = dataset.description
        if dataset.description is not None:
            if len(dataset.description) > 80:
                text += f"<p>{dataset.description[:79]}…</p>"
            else:
                text += f"<p>{dataset.description}</p>"

        if dataset.status != "available":
            status = self.tr("Status:")
            text += f"<p><b>{status}</b> {dataset.status}</p>"

        return text

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return None

        node = self.index2node(index)

        if role == Roles.RoleNodeType:
            if node is not None:
                return node.node_type
            else:
                None

        is_favorite_node = False
        if node is not None:
            is_favorite_node = node.node_type == NodeType.NodeFavorite

        dataset = self.dataset_for_index(index)

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                if dataset is not None:
                    return dataset.title
                elif node.node_type == NodeType.NodeCategory:
                    return node.category
                elif node.node_type == NodeType.NodeCollection:
                    return node.title
                elif is_favorite_node:
                    return self.tr("Favorites")
                return None
            return None
        elif role == Qt.ItemDataRole.ToolTipRole:
            if dataset is not None:
                return self.tooltip_for_dataset(dataset)
            elif node.node_type == NodeType.NodeCategory:
                return node.category
            elif node.node_type == NodeType.NodeCollection:
                return node.title
            elif node.node_type == NodeType.NodeOwner:
                return node.owner
            return None
        elif role == Qt.ItemDataRole.ForegroundRole:
            if dataset is not None:
                if dataset.status == "unavailable":
                    return QBrush(QColor("#d65253"))
                elif dataset.status == "partly":
                    return QBrush(QColor("#eab700"))
                else:
                    return None
            return None
        elif role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:
                if dataset is not None:
                    if dataset.status == "unavailable":
                        return QgsApplication.getThemeIcon("/mTaskCancel.svg")
                    elif dataset.status == "partly":
                        return QgsApplication.getThemeIcon("/mIconWarning.svg")
                    else:
                        return dataset.thumbnail
                elif node.node_type == NodeType.NodeCategory:
                    return PLUGIN_ICON if node.icon is None else node.icon
                elif node.node_type == NodeType.NodeCollection:
                    return PLUGIN_ICON if node.icon is None else node.icon
                elif node.node_type == NodeType.NodeOwner:
                    return PLUGIN_ICON
                elif is_favorite_node:
                    return QgsApplication.getThemeIcon("/mIconFavorites.svg")
                return None
            return None
        elif role == Roles.RoleDatasetUid:
            if index.column() == 0:
                if dataset is not None:
                    return dataset.uid
                return None
            return None
        elif role == Roles.RoleDatasetTitle:
            if index.column() == 0:
                if dataset is not None:
                    return dataset.title
                return None
            return None
        elif role == Roles.RoleDatasetDescription:
            if index.column() == 0:
                if dataset is not None:
                    return dataset.description
                return None
            return None
        elif role == Roles.RoleDatasetTags:
            if index.column() == 0:
                if dataset is not None:
                    return dataset.tags
                return None
            return None

        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        node = self.index2node(parent)
        if node is None:
            return 0

        return len(node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        node = self.index2node(parent)
        if node is None:
            return QModelIndex()

        return self.createIndex(row, column, node.children[row])

    def parent(self, child: QModelIndex) -> QModelIndex:
        if not child.isValid():
            return QModelIndex()

        node = self.index2node(child)
        if node is not None:
            return self.index_of_parent_tree_node(node.parent)
        else:
            return QModelIndex()

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        pass

    def dataset_for_index(self, index: QModelIndex) -> Union[Dataset, None]:
        """
        Returns the dataset which corresponds to a given index, or None
        if the index does not represent a dataset.
        """
        node = self.index2node(index)
        if node is None or node.node_type != NodeType.NodeDataset:
            return None

        return node.dataset

    def is_dataset(self, index: QModelIndex) -> bool:
        """
        Returns True if index corresponds to a dataset.
        """
        node = self.index2node(index)
        return node is not None and node.node_type == NodeType.NodeDataset

    def collection_for_index(
        self, index: QModelIndex
    ) -> Union[Collection, None]:
        """
        Returns a collection which corresponds to a given index, or None
        if the index does not represent a collection.
        """
        node = self.index2node(index)
        if node is None or node.node_type != NodeType.NodeCollection:
            return None

        return node.collection

    def is_collection(self, index: QModelIndex) -> bool:
        """
        Returns True if index corresponds to a collection.
        """
        node = self.index2node(index)
        return node is not None and node.node_type == NodeType.NodeCollection

    def index_of_parent_tree_node(
        self, parent_node: Type[ModelNode]
    ) -> QModelIndex:
        """
        Returns the index corresponding to the parent of a given node.
        """
        grand_parent_node = parent_node.parent
        if grand_parent_node is None:
            return QModelIndex()

        row = grand_parent_node.children.index(parent_node)
        return self.createIndex(row, 0, parent_node)


class DatasetProxyModel(QSortFilterProxyModel):
    """
    A sort/filter proxy model for datasets shown within the DMP Catalogue
    widget, which automatically sorts the data in a logical fashion and
    supports filtering the results.
    """

    def __init__(self, parent=None, registry=None):
        super(DatasetProxyModel, self).__init__(parent)

        self.model = DatasetItemModel(self, registry)
        self.filter_string = ""
        self.filters = None

        self.setSourceModel(self.model)
        self.setDynamicSortFilter(True)
        self.setSortLocaleAware(True)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.sort(0)

        self.model.favoriteAdded.connect(self.invalidateFilter)

    def datasets_model(self) -> DatasetItemModel:
        """
        Returns the underlying source dataset item model.
        """
        return self.model

    def set_filters(self, filters):
        """
        Set filters that affect how catalogue content is filtered.
        """
        self.filters = filters
        self.invalidateFilter()

    def set_filter_string(self, filter_string: str):
        """
        Sets a filter string, such that only algorithms matching the specified
        string will be shown. Matches are performed using a variety of tests,
        including checking against the dataset title, description, tags, etc.
        """
        self.filter_string = filter_string
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        source_index = self.model.index(source_row, 0, source_parent)
        if self.model.is_dataset(source_index):
            if self.filter_string.strip() != "":
                ds_uid = self.sourceModel().data(
                    source_index, Roles.RoleDatasetUid
                )
                ds_descr = self.sourceModel().data(
                    source_index, Roles.RoleDatasetDescription
                )
                ds_tags = self.sourceModel().data(
                    source_index, Roles.RoleDatasetTags
                )
                ds_owners = self.model.dataset_for_index(source_index).owners

                parent_text = list()
                parent = source_index.parent()
                while parent.isValid():
                    parent_parts = (
                        self.sourceModel()
                        .data(parent, Qt.ItemDataRole.DisplayRole)
                        .split(" ")
                    )
                    if parent_parts:
                        parent_text.extend(parent_parts)
                    parent = parent.parent()

                parts_to_match = self.filter_string.strip().split(" ")

                parts_to_search = (
                    self.sourceModel()
                    .data(source_index, Qt.ItemDataRole.DisplayRole)
                    .split(" ")
                )
                parts_to_search.append(ds_uid)
                if ds_tags:
                    parts_to_search.extend(ds_tags)
                if ds_descr:
                    parts_to_search.extend(ds_descr.split(" "))
                parts_to_search.extend(parent_text)
                parts_to_search.extend(ds_owners)

                for part in parts_to_match:
                    found = False
                    for part_to_search in parts_to_search:
                        if part.lower() in part_to_search.lower():
                            found = True
                            break

                    if not found:
                        return False

            if self.filters is not None:
                if self.filters == Filters.ShowOws:
                    return self.model.dataset_for_index(
                        source_index
                    ).has_ows_source()
                if self.filters == Filters.ShowFiles:
                    return self.model.dataset_for_index(
                        source_index
                    ).has_files()

            return True

        has_children = False
        # categories/owners are shown only if they have visible children
        count = self.sourceModel().rowCount(source_index)
        for i in range(count):
            if self.filterAcceptsRow(i, source_index):
                has_children = True
                break

        return has_children

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        left_type = self.sourceModel().data(left, Roles.RoleNodeType)
        right_type = self.sourceModel().data(right, Roles.RoleNodeType)

        if left_type == NodeType.NodeFavorite:
            return True
        elif right_type == NodeType.NodeFavorite:
            return False
        elif left_type != right_type:
            if left_type == NodeType.NodeCategory:
                return False
            if right_type == NodeType.NodeCategory:
                return True
            if left_type == NodeType.NodeCollection:
                return False
            else:
                return True

        # default mode is alphabetical order
        left_str = self.sourceModel().data(left)
        right_str = self.sourceModel().data(right)
        return strcoll(left_str, right_str) < 0

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        return super(DatasetProxyModel, self).data(index, role)
