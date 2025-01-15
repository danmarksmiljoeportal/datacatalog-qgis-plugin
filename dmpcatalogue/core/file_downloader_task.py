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

from qgis.PyQt.QtCore import pyqtSignal, QEventLoop, QUrl

from qgis.core import QgsTask, QgsFileDownloader


class FileDownloaderTask(QgsTask):
    """
    Downloads a file from the given URL and saves it in the specified location.
    Emits downloaded signal when done. If download failed, errors will contain
    error message.
    """

    downloaded = pyqtSignal()

    def __init__(self, url, file_name):
        super(FileDownloaderTask, self).__init__()

        self.url = url
        self.file_name = file_name
        self.downloader = None
        self.errors = None

    def run(self):
        loop = QEventLoop()

        downloader = QgsFileDownloader(QUrl(self.url), self.file_name, "", True)
        downloader.downloadError.connect(
            lambda errors: self.error_occured(errors, loop)
        )
        downloader.downloadProgress.connect(self.update_progress)
        downloader.downloadExited.connect(loop.quit)

        downloader.startDownload()

        try:
            loop.exec_()
        except AttributeError:
            loop.exec()

        if not self.isCanceled():
            self.setProgress(100)

        self.downloaded.emit()

        return not self.isCanceled() and self.errors is None

    def cancel(self):
        if self.downloader is not None:
            self.downloader.cancelDownload()

        super(FileDownloaderTask, self).cancel()

    def error_occured(self, errors, loop):
        self.errors = errors
        loop.quit()

    def update_progress(self, received, total):
        if total > 0:
            self.setProgress((received * 100) / total)
