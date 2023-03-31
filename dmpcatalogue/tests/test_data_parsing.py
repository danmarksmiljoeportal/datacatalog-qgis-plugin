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
import json

from qgis.testing import start_app, unittest

from dmpcatalogue.core.data_classes import WmsSource, WfsSource, WmtsSource
from dmpcatalogue.core.utils import (
    lookup_map,
    resource,
    flatten,
    attribute,
    ows_datasource,
    file_datasource,
    collection,
)

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "testdata")


class test_utils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_app()

    def test_lookup_map(self):
        data_file = os.path.join(TEST_DATA_PATH, "datasets.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        self.assertIn("included", content)
        self.assertIsInstance(content["included"], list)

        transformed = lookup_map(content["included"])
        self.assertIsInstance(transformed, dict)
        self.assertEqual(len(transformed), len(content["included"]))
        for k, v in transformed.items():
            self.assertIsInstance(k, tuple)
            self.assertIsInstance(v, dict)
            self.assertEqual(len(k), 2)

        item = transformed[
            ("wmsSources", "e6d0bc70-2609-478b-89f5-af7200f50f38")
        ]
        self.assertEqual(item["layer"], "dai:aftarea_grvbes")
        self.assertIsNone(item["style"])

        item = transformed[("tags", "1ace4d5b-b3c9-4e77-be35-af7200f50759")]
        self.assertEqual(item["name"], "grundvand")

        item = transformed[
            ("fileSources", "40fb1828-560a-42ce-b08b-af7200f50f38")
        ]
        self.assertNotIn("fileSourceType", item)

        # simplify
        transformed = lookup_map(content["included"], simplify=True)
        item = transformed[
            ("fileSources", "40fb1828-560a-42ce-b08b-af7200f50f38")
        ]
        self.assertIn("fileSourceType", item)
        self.assertEqual(item["fileSourceType"]["name"], "TAB")

        # exclude resource type
        transformed = lookup_map(content["included"], True)
        self.assertIsInstance(transformed, dict)
        self.assertEqual(len(transformed), len(content["included"]))
        for k, v in transformed.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, dict)

        item = transformed["e6d0bc70-2609-478b-89f5-af7200f50f38"]
        self.assertEqual(item["layer"], "dai:aftarea_grvbes")
        self.assertIsNone(item["style"])

        item = transformed["1ace4d5b-b3c9-4e77-be35-af7200f50759"]
        self.assertEqual(item["name"], "grundvand")

        data_file = os.path.join(TEST_DATA_PATH, "collections.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        self.assertIn("included", content)
        self.assertIsInstance(content["included"], list)

        transformed = lookup_map(content["included"], include_resources=True)
        item = transformed[
            ("datasetCollectionItems", "ccafb342-9c14-408e-06e3-08daf51f252b")
        ]
        self.assertIn("dataset", item)
        self.assertIsInstance(item["dataset"], dict)
        self.assertEqual(item["dataset"]["data"]["id"], "urn:dmp:ds:1-test")

    def test_resource(self):
        data_file = os.path.join(TEST_DATA_PATH, "datasets.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        transformed = lookup_map(content["included"])

        res = resource(None, transformed)
        self.assertIsNone(res)

        d = {
            "type": "wmtsSources",
            "id": "5a522420-3878-4bdc-ab21-af7200f50f54",
        }
        res = resource(d, transformed)
        self.assertIsNone(res)

        d = {"type": "wmsSources", "id": "5a522420-3878-4bdc-ab21-af7200f50f54"}
        res = resource(d, transformed)
        self.assertIsInstance(res, dict)
        self.assertEqual(
            res["url"],
            "https://b0902-prod-dist-app.azurewebsites.net/geoserver/wms",
        )
        self.assertEqual(res["layer"], "dai:aa_bes_linjer")

        d = [
            {"type": "tags", "id": "41cfe7cf-c69b-420c-8865-af7200f50759"},
            {"type": "tags", "id": "21048da8-fe93-40ca-a850-af7200f50759"},
            {"type": "tags", "id": "dd9dd252-7c52-4249-b4b6-af7200f50759"},
            {"type": "tags", "id": "da134564-6d7e-4330-ba51-af7200f50759"},
        ]
        res = resource(d, transformed)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 4)
        for item in res:
            self.assertIsInstance(item, dict)
        self.assertEqual(res[0], {"name": "naturbeskyttelsesloven"})
        self.assertEqual(res[1], {"name": "beskyttelseslinje"})
        self.assertEqual(res[2], {"name": "naturbeskyttelse"})
        self.assertEqual(res[3], {"name": "åbeskyttelse"})

    def test_flatten(self):
        data_file = os.path.join(TEST_DATA_PATH, "datasets.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        lookup = lookup_map(content["included"], simplify=True)
        flatten(content["data"], lookup)
        data = content["data"]
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

        for item in data:
            self.assertIsInstance(item, dict)
            self.assertIn("attributes", item)
            self.assertNotIn("relationships", item)

            attributes = item["attributes"]
            self.assertIn("wfsSource", attributes)
            self.assertIn("wmsSource", attributes)
            self.assertIn("wmtsSource", attributes)
            self.assertIn("fileSources", attributes)
            self.assertIn("tags", attributes)
            self.assertIn("owners", attributes)
            self.assertIn("category", attributes)
            self.assertIn("thumbnail", attributes)

        attributes = data[0]["attributes"]
        attr = attributes["wmsSource"]
        self.assertIsInstance(attr, dict)
        self.assertIn("url", attr)
        self.assertIn("layer", attr)
        self.assertIn("style", attr)

        attr = attributes["tags"]
        self.assertIsInstance(attr, list)
        self.assertEqual(len(attr), 4)
        for item in attr:
            self.assertIsInstance(item, dict)
            self.assertEqual(len(item), 1)
            self.assertIn("name", item)

    def test_attribute(self):
        data_file = os.path.join(TEST_DATA_PATH, "datasets.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        lookup = lookup_map(content["included"], simplify=True)
        flatten(content["data"], lookup)
        data = content["data"]

        attrs = data[0]["attributes"]
        self.assertIsInstance(attrs["wmsSource"], dict)
        a = attribute(attrs["wmsSource"], "layer")
        self.assertIsInstance(a, str)
        self.assertEqual(a, "dai:aa_bes_linjer")

        self.assertIsInstance(attrs["tags"], list)
        a = attribute(attrs["tags"], "name")
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 4)
        self.assertEqual(a[0], "naturbeskyttelsesloven")
        self.assertEqual(a[1], "beskyttelseslinje")
        self.assertEqual(a[2], "naturbeskyttelse")
        self.assertEqual(a[3], "åbeskyttelse")

    def test_ows_datasource(self):
        data_file = os.path.join(TEST_DATA_PATH, "datasets.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        lookup = lookup_map(content["included"], simplify=True)
        flatten(content["data"], lookup)
        data = content["data"]

        wfs = data[0]["attributes"]["wfsSource"]
        keys = ["typeName"]
        source = ows_datasource("wfs", wfs, keys)
        self.assertIsInstance(source, WfsSource)

        wms = data[0]["attributes"]["wmsSource"]
        keys = ["layer", "style", "format"]
        source = ows_datasource("wms", wms, keys)
        self.assertIsInstance(source, WmsSource)

        wmts = data[0]["attributes"]["wmtsSource"]
        keys = ["layer", "style", "format", "matrixSet"]
        source = ows_datasource("wmts", wmts, keys)
        self.assertIsInstance(source, WmtsSource)

        source = ows_datasource("wmts", None, keys)
        self.assertIsNone(source)

        # explicitly pass url key
        wfs = data[0]["attributes"]["wfsSource"]
        keys = ["url", "typeName"]
        source = ows_datasource("wfs", wfs, keys)
        self.assertIsInstance(source, WfsSource)

    def test_file_datasource(self):
        data_file = os.path.join(TEST_DATA_PATH, "datasets.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        lookup = lookup_map(content["included"], simplify=True)
        flatten(content["data"], lookup)
        data = content["data"]

        file_sources = data[1]["attributes"]["fileSources"]
        files = file_datasource(file_sources)
        self.assertEqual(len(files), len(file_sources))
        self.assertEqual(
            files[0].url,
            "https://arealdata-api.miljoeportal.dk/data/vanda-ue-33/file",
        )
        self.assertEqual(files[0].file_type, "CSV")

        files = file_datasource(None)
        self.assertIsNone(files)

        files = file_datasource([])
        self.assertIsInstance(files, list)
        self.assertEqual(len(files), 0)

    def test_collection(self):
        data_file = os.path.join(TEST_DATA_PATH, "collections.json")
        with open(data_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        lookup_table = lookup_map(content["included"], include_resources=True)
        item = content["data"][0]
        attributes = collection(item, lookup_table)

        self.assertIn("datasets", attributes)
        datasets = attributes["datasets"]
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0], "urn:dmp:ds:1-test")

        item = content["data"][1]
        attributes = collection(item, lookup_table)

        self.assertIn("datasets", attributes)
        datasets = attributes["datasets"]
        self.assertEqual(len(datasets), 2)
        self.assertEqual(datasets[0], "urn:dmp:ds:aftaleomraader-for-grundvand")
        self.assertEqual(datasets[1], "urn:dmp:ds:bundfauna-dvfi-vandloeb")
