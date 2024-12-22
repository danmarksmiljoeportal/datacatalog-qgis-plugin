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
from dataclasses import dataclass

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QUrl, QUrlQuery

from qgis.core import QgsDataSourceUri, QgsRasterLayer, QgsVectorLayer

from dmpcatalogue.core.settings_registry import SettingsRegistry


@dataclass
class Datasource:
    """
    Base class for all datasources.
    """

    url: str

    def prepare_url(self) -> str:
        """
        Prepares datasource URL for further manipulations. This includes:
          - converting from percent encoding
          - overriding auth for datafordeler.dk and dataforsyningen.dk if
            requested
        """
        url = QUrl.fromPercentEncoding(bytes(self.url, "utf-8"))

        if (
            "datafordeler.dk" in url
            and SettingsRegistry.override_datafordeler_auth()
        ):
            u = QUrl(url)
            if u.hasQuery():
                query = QUrlQuery(u.query())
                if query.hasQueryItem("username") and query.hasQueryItem(
                    "password"
                ):
                    login, password = SettingsRegistry.datafordeler_auth()
                    query.setQueryItems(
                        [("username", login), ("password", password)]
                    )
                    u.setQuery(query)
                    url = u.toString()

        if (
            "dataforsyningen.dk" in url
            and SettingsRegistry.override_dataforsyningen_auth()
        ):
            u = QUrl(url)
            if u.hasQuery():
                query = QUrlQuery(u.query())
                if query.hasQueryItem("token"):
                    token = SettingsRegistry.dataforsyningen_token()
                    query.setQueryItems([("token", token)])
                    u.setQuery(query)
                    url = u.toString()

        return url

    def to_layer(self):
        """
        Converts datasource into a corresponding QgsMapLayer subclass. Should
        be implemented in subclasses.
        """
        raise NotImplementedError("Needs to be implemented by subclasses.")


@dataclass
class WmsSource(Datasource):
    """
    Represents a WMS datasource.
    """

    layer: str
    style: str
    image_format: str

    def to_layer(self, title: str) -> QgsRasterLayer:
        url = self.prepare_url()

        uri = QgsDataSourceUri()
        uri.setParam("url", url)
        uri.setParam("layers", self.layer)
        uri.setParam("styles", self.style)
        uri.setParam("format", self.image_format)
        uri.setParam("crs", "EPSG:25832")
        layer = QgsRasterLayer(str(uri.encodedUri(), "utf-8"), title, "wms")
        return layer


@dataclass
class WmtsSource(WmsSource):
    """
    Represents a WMTS datasource.
    """

    tile_matrix: str

    def to_layer(self, title: str) -> QgsRasterLayer:
        url = self.prepare_url()

        if not all(
            i.casefold() in url.casefold()
            for i in ("SERVICE=WMTS", "REQUEST=GetCapabilities")
        ):
            if "?" not in url:
                url += "?"
            elif url[-1] != "?" and url[-1] != "&":
                url += "&"

            if "SERVICE=WMTS".casefold() not in url.casefold():
                url += "SERVICE=WMTS&"
            if "REQUEST=GetCapabilities".casefold() not in url.casefold():
                url += "REQUEST=GetCapabilities"

        uri = QgsDataSourceUri()
        uri.setParam("url", url)
        uri.setParam("layers", self.layer)
        uri.setParam("styles", self.style)
        uri.setParam("format", self.image_format)
        uri.setParam("tileMatrixSet", self.tile_matrix)
        uri.setParam("crs", "EPSG:25832")
        layer = QgsRasterLayer(str(uri.encodedUri(), "utf-8"), title, "wms")
        return layer


@dataclass
class WfsSource(Datasource):
    """
    Represents a WFS datasource.
    """

    typename: str

    def to_layer(self, title: str) -> QgsVectorLayer:
        url = self.prepare_url()

        uri = QgsDataSourceUri()
        uri.setParam("url", url)
        uri.setParam("typename", self.typename)
        uri.setParam("srsname", "EPSG:25832")
        if SettingsRegistry.use_request_bbox():
            uri.setParam("restrictToRequestBBOX", "1")

        layer = QgsVectorLayer(uri.uri(), title, "wfs")
        return layer


@dataclass
class FileSource(Datasource):
    file_type: str


@dataclass
class Dataset:
    """
    Represents a dataset.
    """

    uid: str
    title: str
    description: str
    category: str
    supportContact: str
    metadata: str
    created: str
    updated: str
    tags: list[str]
    owners: list[str]
    status: str
    thumbnail: QIcon
    category_icon: QIcon
    wms: WmsSource
    wmts: WmtsSource
    wfs: WfsSource
    files: list[str]

    def layer(
        self, protocol: str = ""
    ) -> Union[QgsRasterLayer, QgsVectorLayer, None]:
        """
        Returns layer from one of the associated OGC-compliant datasources.
        If dataset has several datasources, they will be checked in order
        of preference defined in the settings and layer will be constructed
        from the first matching datasource.S
        Returns None if dataset does not contain any OGC-compliant datasources.
        """
        if protocol != "":
            source = getattr(self, protocol)
        else:
            load_order = SettingsRegistry.datasource_load_order()
            for p in load_order:
                source = getattr(self, p)
                if source is not None:
                    break

        if source is not None:
            layer = source.to_layer(self.title)
            self.update_metadata(layer)
            return layer

        return None

    def update_metadata(self, layer: Union[QgsRasterLayer, QgsVectorLayer]):
        """
        Updates layer metadata with the relevant information.
        """
        if layer is None:
            return

        md = layer.metadata()
        md.setIdentifier(self.uid)
        md.setTitle(self.title)
        md.setAbstract(self.description)
        md.setLanguage("DA")
        layer.setMetadata(md)

    def has_ows_source(self) -> bool:
        """
        Returns True if dataset contains OWS sources.
        """
        return any(getattr(self, p) is not None for p in ("wms", "wfs", "wmts"))

    def has_files(self) -> bool:
        """
        Returns True if dataset contains file sources.
        """
        return self.files is not None and len(self.files) > 0


@dataclass
class Collection:
    """
    Represents a collection.
    """

    uid: str
    title: str
    description: str
    datasets: list[str]
    icon: QIcon
