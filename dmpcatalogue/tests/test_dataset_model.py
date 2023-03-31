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

from qgis.testing import start_app, unittest

from qgis.PyQt.QtCore import Qt, QModelIndex, QItemSelectionModel

from dmpcatalogue.core.data_registry import DataRegistry
from dmpcatalogue.gui.dataset_tree_view import DatasetTreeView
from dmpcatalogue.gui.dataset_item_model import (
    DatasetItemModel,
    DatasetProxyModel,
    CategoryNode,
    NodeType,
    Roles,
    Filters,
    Mode,
)


class DummyDataset:
    def __init__(
        self,
        uid,
        title,
        description,
        category,
        tags,
        owners,
        ows=False,
        files=False,
    ):
        self.uid = uid
        self.title = title
        self.description = description
        self.category = category
        self.tags = tags
        self.ows = ows
        self.files = files
        self.status = "available"
        self.thumbnail = None
        self.owners = owners

    def has_ows_source(self):
        return self.ows

    def has_files(self):
        return self.files


class DummyCollection:
    def __init__(self, uid, title, description, datasets):
        self.uid = uid
        self.title = title
        self.description = description
        self.datasets = datasets


class test_dataset_model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_app()

    def test_model(self):
        registry = DataRegistry()
        model = DatasetItemModel(None, registry)

        self.assertEqual(model.mode, Mode.GroupCategories)
        self.assertEqual(model.show_collections, False)
        self.assertEqual(model.columnCount(), 1)
        self.assertEqual(model.rowCount(), 1)
        self.assertTrue(model.hasChildren())
        self.assertEqual(
            model.data(model.index(0, 0, QModelIndex()), Qt.DisplayRole),
            "Favorites",
        )
        self.assertEqual(model.rowCount(model.index(0, 0, QModelIndex())), 0)
        self.assertFalse(
            model.dataset_for_index(model.index(0, 0, QModelIndex()))
        )
        self.assertFalse(
            model.dataset_for_index(model.index(1, 0, QModelIndex()))
        )
        # root node
        self.assertTrue(model.index2node(QModelIndex()))
        self.assertEqual(
            model.index2node(QModelIndex()).node_type, NodeType.NodeCategory
        )
        # root node
        self.assertTrue(model.index2node(model.index(-1, 0, QModelIndex())))
        self.assertEqual(
            model.index2node(QModelIndex()),
            model.index2node(model.index(-1, 0, QModelIndex())),
        )

        # add dataset
        registry.datasets["ds-01"] = DummyDataset(
            "ds-01",
            "dataset1",
            "dataset1 description",
            "category1",
            ["tag1", "tag2"],
            ["org1"],
        )
        model.rebuild()
        self.assertEqual(model.rowCount(), 2)
        self.assertTrue(model.hasChildren())
        self.assertTrue(model.index(0, 0, QModelIndex()).isValid())
        self.assertTrue(model.index(1, 0, QModelIndex()).isValid())
        self.assertEqual(
            model.data(model.index(0, 0, QModelIndex()), Qt.DisplayRole),
            "Favorites",
        )
        self.assertFalse(
            model.dataset_for_index(model.index(1, 0, QModelIndex()))
        )
        self.assertFalse(
            model.dataset_for_index(model.index(2, 0, QModelIndex()))
        )

        category_index = model.index(1, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertTrue(model.hasChildren(category_index))
        self.assertEqual(
            model.data(category_index, Qt.DisplayRole), "category1"
        )
        self.assertEqual(
            model.data(category_index, Qt.ToolTipRole), "category1"
        )
        self.assertFalse(
            model.data(model.index(2, 0, QModelIndex()), Qt.DisplayRole)
        )
        self.assertFalse(
            model.data(model.index(2, 0, QModelIndex()), Qt.ToolTipRole)
        )

        # another dataset
        registry.datasets["ds-02"] = DummyDataset(
            "ds-02",
            "dataset2",
            "dataset2 description",
            "category2",
            ["tag1", "tag3"],
            ["org2"],
        )
        registry.datasets["ds-03"] = DummyDataset(
            "ds-03",
            "dataset3",
            "dataset3 description",
            "category2",
            ["tag2", "tag4"],
            ["org1", "org2"],
        )
        model.rebuild()
        self.assertEqual(model.rowCount(), 3)
        self.assertTrue(model.hasChildren())
        self.assertTrue(model.index(2, 0, QModelIndex()).isValid())

        category_index = model.index(2, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 2)
        self.assertTrue(model.hasChildren(category_index))
        self.assertEqual(
            model.data(category_index, Qt.DisplayRole), "category2"
        )
        self.assertEqual(
            model.data(category_index, Qt.ToolTipRole), "category2"
        )
        self.assertFalse(
            model.data(model.index(3, 0, QModelIndex()), Qt.DisplayRole)
        )
        self.assertFalse(
            model.data(model.index(3, 0, QModelIndex()), Qt.ToolTipRole)
        )

        category_index = model.index(1, 0, QModelIndex())
        ds_index = model.index(0, 0, category_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-01")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset1")
        self.assertEqual(
            model.data(ds_index, Qt.ToolTipRole),
            "<p><b>dataset1</b></p><p>dataset1 description</p>",
        )
        self.assertEqual(model.data(ds_index, Roles.RoleDatasetUid), "ds-01")
        self.assertEqual(
            model.data(ds_index, Roles.RoleDatasetTitle), "dataset1"
        )
        self.assertEqual(
            model.data(ds_index, Roles.RoleDatasetDescription),
            "dataset1 description",
        )
        self.assertEqual(
            ",".join(model.data(ds_index, Roles.RoleDatasetTags)), "tag1,tag2"
        )

        category_index = model.index(2, 0, QModelIndex())
        ds_index = model.index(0, 0, category_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-02")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset2")
        self.assertEqual(
            model.data(ds_index, Qt.ToolTipRole),
            "<p><b>dataset2</b></p><p>dataset2 description</p>",
        )
        self.assertEqual(model.data(ds_index, Roles.RoleDatasetUid), "ds-02")
        self.assertEqual(
            model.data(ds_index, Roles.RoleDatasetTitle), "dataset2"
        )
        self.assertEqual(
            model.data(ds_index, Roles.RoleDatasetDescription),
            "dataset2 description",
        )
        self.assertEqual(
            ",".join(model.data(ds_index, Roles.RoleDatasetTags)), "tag1,tag3"
        )

        # dataset without category
        registry.datasets["ds-04"] = DummyDataset(
            "ds-04", "dataset4", "dataset4 description", "", ["tag4"], ["org1"]
        )
        model.rebuild()
        self.assertEqual(model.rowCount(), 4)
        self.assertTrue(model.hasChildren())
        self.assertTrue(model.index(3, 0, QModelIndex()).isValid())
        self.assertTrue(
            model.dataset_for_index(model.index(3, 0, QModelIndex()))
        )
        ds_index = model.index(3, 0, QModelIndex())
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-04")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset4")
        self.assertEqual(
            model.data(ds_index, Qt.ToolTipRole),
            "<p><b>dataset4</b></p><p>dataset4 description</p>",
        )
        self.assertEqual(model.data(ds_index, Roles.RoleDatasetUid), "ds-04")
        self.assertEqual(
            model.data(ds_index, Roles.RoleDatasetTitle), "dataset4"
        )
        self.assertEqual(
            model.data(ds_index, Roles.RoleDatasetDescription),
            "dataset4 description",
        )
        self.assertEqual(
            ",".join(model.data(ds_index, Roles.RoleDatasetTags)), "tag4"
        )

        # favorites
        favorites_index = model.index(0, 0, QModelIndex())
        self.assertEqual(
            model.data(favorites_index, Qt.DisplayRole), "Favorites"
        )
        self.assertEqual(model.rowCount(favorites_index), 0)
        registry.add_or_remove_favorite("ds-02")
        self.assertEqual(model.rowCount(favorites_index), 1)
        self.assertEqual(
            model.data(
                model.index(0, 0, favorites_index), Roles.RoleDatasetUid
            ),
            "ds-02",
        )
        registry.add_or_remove_favorite("ds-04")
        self.assertEqual(model.rowCount(favorites_index), 2)
        self.assertEqual(
            model.data(
                model.index(1, 0, favorites_index), Roles.RoleDatasetUid
            ),
            "ds-04",
        )

        # clear favorites
        registry.add_or_remove_favorite("ds-02")
        self.assertEqual(model.rowCount(favorites_index), 1)
        self.assertEqual(
            model.data(
                model.index(0, 0, favorites_index), Roles.RoleDatasetUid
            ),
            "ds-04",
        )
        registry.add_or_remove_favorite("ds-04")
        self.assertEqual(model.rowCount(favorites_index), 0)

        # group by owner
        model.set_mode(Mode.GroupOwners)
        self.assertEqual(model.mode, Mode.GroupOwners)
        self.assertEqual(model.rowCount(), 3)
        self.assertTrue(model.hasChildren())
        self.assertTrue(model.index(0, 0, QModelIndex()).isValid())
        self.assertTrue(model.index(1, 0, QModelIndex()).isValid())
        self.assertTrue(model.index(2, 0, QModelIndex()).isValid())

        self.assertTrue(model.index2node(QModelIndex()))
        self.assertEqual(
            model.index2node(QModelIndex()).node_type, NodeType.NodeOwner
        )

        self.assertEqual(
            model.data(model.index(0, 0, QModelIndex()), Qt.DisplayRole),
            "Favorites",
        )
        self.assertEqual(model.rowCount(model.index(0, 0, QModelIndex())), 0)

        owner_index = model.index(1, 0, QModelIndex())
        self.assertTrue(model.hasChildren(owner_index))
        self.assertEqual(model.rowCount(owner_index), 3)
        self.assertEqual(model.data(owner_index, Qt.DisplayRole), "org1")
        self.assertEqual(model.data(owner_index, Qt.ToolTipRole), "org1")

        ds_index = model.index(0, 0, owner_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-01")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset1")
        ds_index = model.index(1, 0, owner_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-03")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset3")
        ds_index = model.index(2, 0, owner_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-04")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset4")

        owner_index = model.index(2, 0, QModelIndex())
        self.assertTrue(model.hasChildren(owner_index))
        self.assertEqual(model.rowCount(owner_index), 2)
        self.assertEqual(model.data(owner_index, Qt.DisplayRole), "org2")
        self.assertEqual(model.data(owner_index, Qt.ToolTipRole), "org2")
        ds_index = model.index(0, 0, owner_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-02")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset2")
        ds_index = model.index(1, 0, owner_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-03")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset3")

        # collections
        model.set_mode(Mode.GroupCategories)
        model.set_show_collections(True)
        self.assertEqual(model.show_collections, True)
        self.assertEqual(model.rowCount(), 1)
        self.assertTrue(model.hasChildren())
        self.assertEqual(
            model.data(model.index(0, 0, QModelIndex()), Qt.DisplayRole),
            "Favorites",
        )
        self.assertEqual(model.rowCount(model.index(0, 0, QModelIndex())), 0)
        self.assertTrue(model.index2node(QModelIndex()))
        self.assertEqual(
            model.index2node(QModelIndex()).node_type, NodeType.NodeCategory
        )

        registry.collections["col-01"] = DummyCollection(
            "col-01",
            "collection1",
            "collection1 description",
            ["ds-01", "ds-02"],
        )
        model.rebuild()
        self.assertEqual(model.rowCount(), 2)
        self.assertTrue(model.hasChildren())
        self.assertTrue(model.index(0, 0, QModelIndex()).isValid())
        self.assertTrue(model.index(1, 0, QModelIndex()).isValid())
        self.assertEqual(
            model.index2node(QModelIndex()).node_type, NodeType.NodeCategory
        )
        self.assertEqual(
            model.data(model.index(0, 0, QModelIndex()), Qt.DisplayRole),
            "Favorites",
        )
        collection_index = model.index(1, 0, QModelIndex())
        self.assertEqual(
            model.index2node(collection_index).node_type,
            NodeType.NodeCollection,
        )
        self.assertTrue(model.hasChildren(collection_index))
        self.assertEqual(model.rowCount(collection_index), 2)
        self.assertEqual(
            model.data(collection_index, Qt.DisplayRole), "collection1"
        )
        self.assertEqual(
            model.data(collection_index, Qt.ToolTipRole), "collection1"
        )

        ds_index = model.index(0, 0, collection_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-01")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset1")
        ds_index = model.index(1, 0, collection_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-02")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset2")

        registry.collections["col-02"] = DummyCollection(
            "col-02",
            "collection2",
            "collection2 description",
            ["ds-01", "ds-03"],
        )
        model.rebuild()
        self.assertEqual(model.rowCount(), 3)

        collection_index = model.index(2, 0, QModelIndex())
        self.assertEqual(
            model.index2node(collection_index).node_type,
            NodeType.NodeCollection,
        )
        self.assertTrue(model.hasChildren(collection_index))
        self.assertEqual(model.rowCount(collection_index), 2)
        self.assertEqual(
            model.data(collection_index, Qt.DisplayRole), "collection2"
        )
        self.assertEqual(
            model.data(collection_index, Qt.ToolTipRole), "collection2"
        )
        ds_index = model.index(0, 0, collection_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-01")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset1")
        ds_index = model.index(1, 0, collection_index)
        self.assertTrue(model.dataset_for_index(ds_index))
        self.assertEqual(model.dataset_for_index(ds_index).uid, "ds-03")
        self.assertEqual(model.data(ds_index, Qt.DisplayRole), "dataset3")

        registry.collections["col-03"] = DummyCollection(
            "col-03",
            "collection3",
            "collection3 description",
            ["ds-05", "ds-06"],
        )
        model.rebuild()
        self.assertEqual(model.rowCount(), 4)

        collection_index = model.index(3, 0, QModelIndex())
        self.assertEqual(
            model.index2node(collection_index).node_type,
            NodeType.NodeCollection,
        )
        self.assertFalse(model.hasChildren(collection_index))
        self.assertEqual(model.rowCount(collection_index), 0)

    def test_proxy_model(self):
        registry = DataRegistry()
        model = DatasetProxyModel(None, registry)

        registry.datasets["ds1"] = DummyDataset(
            "ds1",
            "dataset1",
            "dataset description",
            "category1",
            ["raster", "landcover"],
            ["org1"],
            True,
            False,
        )
        registry.datasets["ds2"] = DummyDataset(
            "ds2",
            "dataset2",
            "dataset2 description",
            "category1",
            ["raster", "elevation"],
            ["org2"],
            True,
            True,
        )
        registry.datasets["ds3"] = DummyDataset(
            "ds3",
            "dataset1-2",
            "some infomative text",
            "category2",
            ["vector", "roads"],
            ["org1"],
            False,
            True,
        )

        model.model.rebuild()
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(
            model.data(model.index(0, 0, QModelIndex()), Qt.DisplayRole),
            "category1",
        )
        self.assertEqual(
            model.data(model.index(1, 0, QModelIndex()), Qt.DisplayRole),
            "category2",
        )

        # filter by dataset id
        model.set_filter_string("ds1")
        self.assertEqual(model.rowCount(), 1)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds1",
        )
        model.set_filter_string("ds")
        self.assertEqual(model.rowCount(), 2)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 2)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds1",
        )
        self.assertEqual(
            model.data(model.index(1, 0, category_index), Roles.RoleDatasetUid),
            "ds2",
        )
        category_index = model.index(1, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds3",
        )

        # filter by title
        model.set_filter_string("dataset1")
        self.assertEqual(model.rowCount(), 2)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds1",
        )

        category_index = model.index(1, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds3",
        )

        # filter by description, empty categories should not be shown
        model.set_filter_string("text")
        self.assertEqual(model.rowCount(), 1)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds3",
        )

        # filter by tags
        model.set_filter_string("elevation")
        self.assertEqual(model.rowCount(), 1)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(
            model.data(model.index(0, 0, category_index), Roles.RoleDatasetUid),
            "ds2",
        )

        model.set_filter_string("raster roads")
        self.assertEqual(model.rowCount(), 0)

        model.set_filter_string("")
        self.assertEqual(model.rowCount(), 2)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 2)
        category_index = model.index(1, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)

        # filter by sources
        model.set_filters(Filters.ShowOws)
        self.assertEqual(model.rowCount(), 1)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 2)

        model.set_filters(Filters.ShowFiles)
        self.assertEqual(model.rowCount(), 2)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)
        category_index = model.index(1, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)

        model.set_filters(Filters.ShowAll)
        self.assertEqual(model.rowCount(), 2)
        category_index = model.index(0, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 2)
        category_index = model.index(1, 0, QModelIndex())
        self.assertEqual(model.rowCount(category_index), 1)

        # favorites
        registry.add_or_remove_favorite("ds2")
        self.assertEqual(model.rowCount(), 3)
        favorites_index = model.index(0, 0, QModelIndex())
        self.assertEqual(
            model.data(favorites_index, Qt.DisplayRole), "Favorites"
        )
        self.assertEqual(model.rowCount(favorites_index), 1)
        self.assertEqual(
            model.data(
                model.index(0, 0, favorites_index), Roles.RoleDatasetUid
            ),
            "ds2",
        )
        registry.add_or_remove_favorite("ds1")
        self.assertEqual(model.rowCount(favorites_index), 2)
        self.assertEqual(
            model.data(
                model.index(0, 0, favorites_index), Roles.RoleDatasetUid
            ),
            "ds1",
        )
        self.assertEqual(
            model.data(
                model.index(1, 0, favorites_index), Roles.RoleDatasetUid
            ),
            "ds2",
        )
        registry.add_or_remove_favorite("ds1")
        registry.add_or_remove_favorite("ds2")

    def test_view(self):
        registry = DataRegistry()
        view = DatasetTreeView(None, registry)

        # check view model consistency
        self.assertTrue(view.proxy_model)
        self.assertTrue(view.datasets_model)
        self.assertEqual(view.proxy_model.datasets_model(), view.datasets_model)

        self.assertFalse(view.dataset_for_index(QModelIndex()))

        # add some data
        registry.datasets["ds1"] = DummyDataset(
            "ds1",
            "dataset1",
            "dataset description",
            "category1",
            ["raster", "landcover"],
            ["org1"],
            True,
            False,
        )
        registry.datasets["ds2"] = DummyDataset(
            "ds2",
            "dataset2",
            "dataset2 description",
            "category1",
            ["raster", "elevation"],
            ["org2"],
            True,
            True,
        )
        registry.datasets["ds3"] = DummyDataset(
            "ds3",
            "dataset1-2",
            "some infomative text",
            "category2",
            ["vector", "roads"],
            ["org1"],
            False,
            True,
        )

        view.datasets_model.rebuild()

        category_index = view.proxy_model.index(0, 0, QModelIndex())
        self.assertFalse(view.dataset_for_index(category_index))
        self.assertEqual(
            view.proxy_model.data(category_index, Qt.DisplayRole), "category1"
        )
        ds_index = view.proxy_model.index(0, 0, category_index)
        self.assertEqual(view.dataset_for_index(ds_index).uid, "ds1")
        category_index = view.proxy_model.index(1, 0, QModelIndex())
        self.assertFalse(view.dataset_for_index(category_index))
        self.assertEqual(
            view.proxy_model.data(category_index, Qt.DisplayRole), "category2"
        )
        ds_index = view.proxy_model.index(0, 0, category_index)
        self.assertEqual(view.dataset_for_index(ds_index).uid, "ds3")

        # test filter strings, empty categories should not be shown
        view.set_filter_string("text")
        category_index = view.proxy_model.index(0, 0, QModelIndex())
        self.assertEqual(
            view.proxy_model.data(category_index, Qt.DisplayRole), "category2"
        )
        self.assertEqual(view.proxy_model.rowCount(), 1)
        self.assertEqual(view.proxy_model.rowCount(category_index), 1)

        view.set_filter_string("")

        # selected dataset
        category_index = view.proxy_model.index(0, 0, QModelIndex())
        view.selectionModel().clear()
        self.assertFalse(view.selected_dataset())
        view.selectionModel().select(
            category_index, QItemSelectionModel.ClearAndSelect
        )
        self.assertFalse(view.selected_dataset())
        ds_index = view.proxy_model.index(0, 0, category_index)
        view.selectionModel().select(
            ds_index, QItemSelectionModel.ClearAndSelect
        )
        self.assertEqual(view.selected_dataset().uid, "ds1")

        # when a filter string removes the selected dataset, the next
        # matching dataset should be auto-selected
        view.set_filter_string("dataset2")
        self.assertEqual(view.selected_dataset().uid, "ds2")
        # but if it doesn't remove the selected one, that dataset should
        # not be deselected
        view.set_filter_string("da")
        self.assertEqual(view.selected_dataset().uid, "ds2")
