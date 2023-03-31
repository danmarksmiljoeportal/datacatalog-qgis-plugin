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

import os
from functools import partial

from qgis.PyQt.QtCore import pyqtSignal, QObject, QUrl
from qgis.PyQt.QtNetwork import QNetworkReply

from qgis.core import QgsApplication, QgsNetworkContentFetcherTask, QgsTask

from dmpcatalogue.core.data_parser_task import DataParserTask
from dmpcatalogue.core.file_downloader_task import FileDownloaderTask
from dmpcatalogue.core.settings_registry import SettingsRegistry
from dmpcatalogue.core.utils import cache_directory, file_exists
from dmpcatalogue.constants import DEFAULT_LOCALE, LOCALES


class DataRegistry(QObject):
    """
    A registry for data from the catalogue.
    """

    initialized = pyqtSignal()
    dataFetched = pyqtSignal()
    requestFailed = pyqtSignal(str)
    favoritesChanged = pyqtSignal()
    fileDownloaded = pyqtSignal(str)
    downloadFailed = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

        self.datasets = dict()
        self.collections = dict()
        self.favorites = SettingsRegistry.favorites()
        self.task_manager = QgsApplication.taskManager()

        locale = QgsApplication.locale()
        self.locale = locale if locale in LOCALES else DEFAULT_LOCALE

        self.dataFetched.connect(self.parse_data)

    def initialize(self, force_download=False):
        """
        Starts data registry initialization. This includes loading data from
        the cache or fetching them from the server, as well as parsing and
        storing in the registry.
        """
        url = SettingsRegistry.catalog_url()

        cache_root = cache_directory()
        status_cache = os.path.join(cache_root, "status.json")
        datasets_cache = os.path.join(cache_root, "datasets.json")
        collections_cache = os.path.join(cache_root, "collections.json")

        if file_exists(datasets_cache) and not force_download:
            # datasets cached, only fetch their status
            task = QgsNetworkContentFetcherTask(
                QUrl(f"{url}/datasetAvailabilities?locale={self.locale}")
            )
            reply_handler = partial(self.cache_response, task, status_cache)
            task.fetched.connect(reply_handler)
            task.errorOccurred.connect(self.report_error)
        else:
            # fetch datasets and their status
            status_task = QgsNetworkContentFetcherTask(
                QUrl(f"{url}/datasetAvailabilities?locale={self.locale}")
            )
            status_reply_handler = partial(
                self.cache_response, status_task, status_cache, False
            )
            status_task.fetched.connect(status_reply_handler)
            status_task.errorOccurred.connect(self.report_error)

            collections_task = QgsNetworkContentFetcherTask(
                QUrl(
                    f"{url}/datasetCollections?include="
                    "datasetCollectionItems,datasetCollectionItems.dataset"
                    f"&locale={self.locale}"
                )
            )
            collections_reply_handler = partial(
                self.cache_response, collections_task, collections_cache, False
            )
            collections_task.fetched.connect(collections_reply_handler)
            collections_task.errorOccurred.connect(self.report_error)

            task = QgsNetworkContentFetcherTask(
                QUrl(
                    f"{url}/datasets?include="
                    "wfsSource,wmsSource,wmtsSource,fileSources,"
                    "category,tags,owners,thumbnail,"
                    "fileSources.fileSourceType"
                    f"&locale={self.locale}"
                )
            )
            task_handler = partial(self.cache_response, task, datasets_cache)
            task.fetched.connect(task_handler)
            task.errorOccurred.connect(self.report_error)
            task.addSubTask(
                collections_task,
                subTaskDependency=QgsTask.ParentDependsOnSubTask,
            )
            task.addSubTask(
                status_task, subTaskDependency=QgsTask.ParentDependsOnSubTask
            )

        self.task_manager.addTask(task)

    def has_error(self, task) -> bool:
        """
        Checks whether network content fetcher task completed without
        error. In case of error emits signal with the error details.
        """
        reply = task.reply()
        if reply is not None:
            if reply.error() != QNetworkReply.NoError:
                self.requestFailed.emit(
                    self.tr("Network request failed: ") + reply.errorString()
                )
                return True

        return False

    def cache_response(self, task, cache_file: str, emit_signal: bool = True):
        """
        Caches server reply. If emit_signal is True, emit dataFetched when
        completed.
        """
        if self.has_error(task):
            return

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(task.contentAsString())

        if emit_signal:
            self.dataFetched.emit()

    def parse_data(self):
        """
        Starts background task to parse data and populate registry.
        """
        task = DataParserTask()
        handler = partial(self.load_data, task)
        task.processed.connect(handler)
        self.task_manager.addTask(task)

    def load_data(self, task):
        self.datasets = task.datasets
        self.collections = task.collections
        self.initialized.emit()

    def add_or_remove_favorite(self, dataset_uid: str):
        """
        Adds or removes dataset with the given UID to/from favorites.
        """
        if dataset_uid not in self.favorites:
            self.favorites.append(dataset_uid)
        else:
            self.favorites.remove(dataset_uid)

        SettingsRegistry.set_favorites(self.favorites)
        self.favoritesChanged.emit()

    def download_file(self, url: str, file_name: str):
        """
        Downloads data from the given URL and saves them to the specified
        location. Emits signal on success and signal on failure.
        """
        task = FileDownloaderTask(url, file_name)
        handler = partial(self.download_finished, task, file_name)
        task.downloaded.connect(handler)
        self.task_manager.addTask(task)

    def download_finished(self, task, file_name: str):
        errors = task.errors
        if errors is None:
            self.fileDownloaded.emit(file_name)
        else:
            self.downloadFailed.emit("\n".join(errors))

    def report_error(self, code, message):
        self.requestFailed.emit(self.tr("Network request failed: ") + message)


DATA_REGISTRY = DataRegistry()
