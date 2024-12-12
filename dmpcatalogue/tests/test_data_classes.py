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

from qgis.PyQt.QtCore import QUrl

from qgis.core import QgsApplication
from qgis.testing import start_app, unittest

from dmpcatalogue.core.data_classes import (
    Datasource,
    WmsSource,
    WmtsSource,
    WfsSource,
    Dataset,
)
from dmpcatalogue.core.settings_registry import SettingsRegistry


class test_classes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start_app()

        auth_manager = QgsApplication.authManager()
        assert auth_manager.setMasterPassword("masterpassword", True)

    def test_datasource(self):
        url = "https://server.com/api?param1=v1&param2=v2"
        encoded = "https%3A%2F%2Fserver.com%2Fapi%3Fparam1%3Dv1%26param2%3Dv2"

        ds = Datasource(encoded)
        out_url = ds.prepare_url()
        self.assertEqual(out_url, url)

        ds.url = url
        out_url = ds.prepare_url()
        self.assertEqual(out_url, url)

        # datafordeler.dk auth
        ds.url = "https://services.datafordeler.dk/DAGIM/dagi/1.0.0/WMS"
        out_url = ds.prepare_url()
        self.assertEqual(out_url, ds.url)

        ds.url = (
            "https://services.datafordeler.dk/DAGIM/dagi/1.0.0/WMS?"
            "username=UFZLDDPIJS&password=DAIdatafordel123"
        )
        out_url = ds.prepare_url()
        self.assertEqual(out_url, ds.url)

        SettingsRegistry.set_datafordeler_auth("test_login", "test_password")
        SettingsRegistry.set_override_datafordeler_auth(True)

        out_url = ds.prepare_url()
        u = QUrl(out_url)
        self.assertTrue(u.hasQuery())
        q = u.query()
        self.assertEqual(q, "username=test_login&password=test_password")

        SettingsRegistry.set_datafordeler_auth("", "")
        out_url = ds.prepare_url()
        u = QUrl(out_url)
        self.assertTrue(u.hasQuery())
        q = u.query()
        self.assertEqual(q, "username=&password=")

        SettingsRegistry.set_override_datafordeler_auth(False)
        out_url = ds.prepare_url()
        u = QUrl(out_url)
        self.assertTrue(u.hasQuery())
        q = u.query()
        self.assertEqual(q, "username=UFZLDDPIJS&password=DAIdatafordel123")

        # override dataforsyningen.dk auth
        ds.url = "https://api.dataforsyningen.dk/dhm_flow_ekstremregn"
        out_url = ds.prepare_url()
        self.assertEqual(out_url, ds.url)

        ds.url = (
            "https://api.dataforsyningen.dk/dhm_flow_ekstremregn?"
            "token=6a51dcd965ebe455153c9da5ceddbab9"
        )
        out_url = ds.prepare_url()
        self.assertEqual(out_url, ds.url)

        SettingsRegistry.set_dataforsyningen_token("test_token")
        SettingsRegistry.set_override_dataforsyningen_auth(True)

        out_url = ds.prepare_url()
        u = QUrl(out_url)
        self.assertTrue(u.hasQuery())
        q = u.query()
        self.assertEqual(q, "token=test_token")

        SettingsRegistry.set_dataforsyningen_token("")
        out_url = ds.prepare_url()
        u = QUrl(out_url)
        self.assertTrue(u.hasQuery())
        q = u.query()
        self.assertEqual(q, "token=")

        SettingsRegistry.set_override_dataforsyningen_auth(False)
        out_url = ds.prepare_url()
        u = QUrl(out_url)
        self.assertTrue(u.hasQuery())
        q = u.query()
        self.assertEqual(q, "token=6a51dcd965ebe455153c9da5ceddbab9")

        with self.assertRaises(NotImplementedError):
            ds.to_layer()

    def test_wms_source(self):
        ds = WmsSource(
            "https://geodata.fvm.dk/geoserver/Vandprojekter/wms",
            "ID15oplande",
            "Vandprojekter:ID15oplande",
            "image/png",
        )

        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

    def test_wmts_source(self):
        ds = WmtsSource(
            "https://tilecache3-miljoegis.mim.dk/gwc/service/wmts",
            "theme-vp3b-2019-vandlob_okotilstand_samlet",
            "default",
            "image/png",
            "EPSG:25832",
        )

        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

        ds.url = "https://tilecache3-miljoegis.mim.dk/gwc/service/wmts?"
        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

        ds.url = (
            "https://tilecache3-miljoegis.mim.dk/gwc/service/wmts?"
            "SERVICE=WMTS"
        )
        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

        ds.url = (
            "https://tilecache3-miljoegis.mim.dk/gwc/service/wmts?"
            "REQUEST=GetCapabilities"
        )
        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

        ds.url = (
            "https://tilecache3-miljoegis.mim.dk/gwc/service/wmts?"
            "REQUEST=GetCapabilities&SERVICE=WMTS"
        )
        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

        ds.url = (
            "https://tilecache3-miljoegis.mim.dk/gwc/service/wmts%3F"
            "SERVICE%3DWMTS%26REQUEST%3DGetCapabilities"
        )
        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

    def test_wfs_source(self):
        ds = WfsSource(
            "https://b0902-prod-dist-app.azurewebsites.net/geoserver/wfs",
            "dai:aa_bes_linjer",
        )

        layer = ds.to_layer("test")
        self.assertTrue(layer.isValid())

    def test_dataset(self):
        ds = Dataset(
            "urn:dmp:ds:aabeskyttelseslinjer",
            "Åbeskyttelseslinjer",
            "Åbeskyttelseslinjen har til formål at sikre åer",
            "Naturbeskyttelse",
            "support@miljoeportal.dk",
            "https://geodata-info.dk/srv/dan/catalog.search/metadata",
            "2022-12-05 12:33:09Z",
            "2022-12-05 12:33:09Z",
            ["åbeskyttelse", "beskyttelseslinje", "naturbeskyttelse"],
            ["Kommunerne"],
            "available",
            None,
            None,
            WmsSource(
                "https://geodata.fvm.dk/geoserver/Vandprojekter/wms",
                "ID15oplande",
                "Vandprojekter:ID15oplande",
                "image/png",
            ),
            None,
            WfsSource(
                "https://b0902-prod-dist-app.azurewebsites.net/geoserver/wfs",
                "dai:aa_bes_linjer",
            ),
            [],
        )

        SettingsRegistry.set_datasource_load_order(["wfs", "wmts", "wms"])
        layer = ds.layer()
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.name(), ds.title)
        self.assertEqual(layer.providerType(), "wfs")
        md = layer.metadata()
        self.assertEqual(md.identifier(), ds.uid)
        self.assertEqual(md.title(), ds.title)
        self.assertEqual(md.abstract(), ds.description)
        self.assertEqual(md.language(), "DA")

        SettingsRegistry.set_datasource_load_order(["wms", "wfs", "wmts"])
        layer = ds.layer()
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.name(), ds.title)
        self.assertEqual(layer.providerType(), "wms")
        md = layer.metadata()
        self.assertEqual(md.identifier(), ds.uid)
        self.assertEqual(md.title(), ds.title)
        self.assertEqual(md.abstract(), ds.description)
        self.assertEqual(md.language(), "DA")

        SettingsRegistry.set_datasource_load_order(["wmts", "wfs", "wms"])
        layer = ds.layer()
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.name(), ds.title)
        self.assertEqual(layer.providerType(), "wfs")
        md = layer.metadata()
        self.assertEqual(md.identifier(), ds.uid)
        self.assertEqual(md.title(), ds.title)
        self.assertEqual(md.abstract(), ds.description)
        self.assertEqual(md.language(), "DA")

        # explicitly specify datasource
        layer = ds.layer("wfs")
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.name(), ds.title)
        self.assertEqual(layer.providerType(), "wfs")

        layer = ds.layer("wmts")
        self.assertIsNone(layer)

        # check for source presence
        self.assertTrue(ds.has_ows_source())
        ds.wms = None
        ds.wfs = None
        ds.wmts = None
        self.assertFalse(ds.has_ows_source())

        self.assertFalse(ds.has_files())
        ds.files = None
        self.assertFalse(ds.has_files())
        ds.files = ["https://server.dk/data/resource/file"]
        self.assertTrue(ds.has_files())
