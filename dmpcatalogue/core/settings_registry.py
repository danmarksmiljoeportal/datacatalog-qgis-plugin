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

from qgis.core import QgsSettings, QgsApplication

from dmpcatalogue.constants import DEFAULT_API_ROOT, DEFAULT_LOAD_ORDER


class SettingsRegistry:
    @staticmethod
    def catalog_url() -> str:
        """
        Returns server URL.
        """
        settings = QgsSettings()
        url = settings.value(
            "dmpcatalogue/url", DEFAULT_API_ROOT, str, QgsSettings.Plugins
        )
        return url

    @staticmethod
    def set_catalog_url(url: str):
        """
        Sets server URL.
        """
        settings = QgsSettings()
        settings.setValue("dmpcatalogue/url", url, QgsSettings.Plugins)

    @staticmethod
    def datasource_load_order() -> list[str]:
        """
        Returns preferred datasource load order.
        """
        settings = QgsSettings()
        order = settings.value(
            "dmpcatalogue/datasource_load_order",
            DEFAULT_LOAD_ORDER,
            list,
            QgsSettings.Plugins,
        )
        return order

    @staticmethod
    def set_datasource_load_order(load_order: list[str]):
        """
        Sets preferred datasource load order.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/datasource_load_order",
            load_order,
            QgsSettings.Plugins,
        )

    @staticmethod
    def override_datafordeler_auth() -> bool:
        """
        Returns Datafordeler auth override flag.
        """
        settings = QgsSettings()
        override = settings.value(
            "dmpcatalogue/override_datafordeler_auth",
            False,
            bool,
            QgsSettings.Plugins,
        )
        return override

    @staticmethod
    def set_override_datafordeler_auth(override: bool):
        """
        Sets Datafordeler auth override flag.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/override_datafordeler_auth",
            override,
            QgsSettings.Plugins,
        )

    @staticmethod
    def datafordeler_auth() -> tuple[str, str]:
        """
        Returns Datafordeler login and password.
        """
        settings = QgsSettings()
        login = settings.value(
            "dmpcatalogue/datafordeler/login", "", str, QgsSettings.Plugins
        )
        password = settings.value(
            "dmpcatalogue/datafordeler/password", "", str, QgsSettings.Plugins
        )
        return login, password

    @staticmethod
    def set_datafordeler_auth(login: str, password: str):
        """
        Sets Datafordeler login and password.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/datafordeler/login", login, QgsSettings.Plugins
        )
        password = settings.setValue(
            "dmpcatalogue/datafordeler/password", password, QgsSettings.Plugins
        )

    @staticmethod
    def override_dataforsyningen_auth() -> bool:
        """
        Returns Dataforsyningen auth override flag.
        """
        settings = QgsSettings()
        override = settings.value(
            "dmpcatalogue/override_dataforsyningen_auth",
            False,
            bool,
            QgsSettings.Plugins,
        )
        return override

    @staticmethod
    def set_override_dataforsyningen_auth(override: bool):
        """
        Sets Dataforsyningen auth override flag.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/override_dataforsyningen_auth",
            override,
            QgsSettings.Plugins,
        )

    @staticmethod
    def dataforsyningen_token() -> str:
        """
        Returns Dataforsyningen token.
        """
        settings = QgsSettings()
        token = settings.value(
            "dmpcatalogue/dataforsyningen/token", "", str, QgsSettings.Plugins
        )
        return token

    @staticmethod
    def set_dataforsyningen_token(token: str):
        """
        Sets Dataforsyningen login and password.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/dataforsyningen/token", token, QgsSettings.Plugins
        )

    @staticmethod
    def favorites() -> list[str]:
        """
        Returns favorite datasets.
        """
        settings = QgsSettings()
        return settings.value(
            "dmpcatalogue/favorites", list(), list, QgsSettings.Plugins
        )

    @staticmethod
    def set_favorites(favorites: list[str]):
        """
        Sets favorite datasets.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/favorites", favorites, QgsSettings.Plugins
        )

    @staticmethod
    def last_used_directory() -> str:
        """
        Returns last used directory for saved files.
        """
        settings = QgsSettings()
        return settings.value(
            "dmpcatalogue/last_dir", None, str, QgsSettings.Plugins
        )

    @staticmethod
    def set_last_used_directory(directory: str):
        """
        Sets last used directory for saved files.
        """
        settings = QgsSettings()
        settings.setValue(
            "dmpcatalogue/last_dir", directory, QgsSettings.Plugins
        )
