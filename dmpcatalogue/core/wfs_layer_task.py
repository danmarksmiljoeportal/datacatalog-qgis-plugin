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

from qgis.PyQt.QtCore import pyqtSignal

from qgis.core import (
    QgsVectorLayer,
    QgsTask,
    QgsApplication,
    QgsNetworkAccessManager,
)


class WfsLayerTask(QgsTask):
    """
    Creates a WFS QgsVectorLayer in a background thread so the GUI remains
    responsive when a server is slow or unresponsive.

    Emits layerReady(layer, error_message) once finished:
      - On success: layer is a valid QgsVectorLayer already moved to the main
        thread, error_message is an empty string.
      - On failure: layer is None, error_message describes what went wrong.
    """

    layerReady = pyqtSignal(object, str)

    # Network timeout applied on the background thread's manager (ms).
    REQUEST_TIMEOUT_MS = 10000
    # No retries: fail after a single attempt so the error surfaces quickly.
    MAX_RETRIES = 0

    def __init__(self, uri_string: str, title: str):
        super().__init__(
            f"Loading layer {title}",
            QgsTask.CanCancel,
        )
        self._uri_string = uri_string
        self._title = title
        self._layer = None
        self._error = None

    def run(self) -> bool:
        if self.isCanceled():
            return False

        # Limit the timeout on this background thread's network manager.
        # Each QgsTask thread has its own QgsNetworkAccessManager instance,
        # so this does not affect other threads or the main GUI thread.
        nam = QgsNetworkAccessManager.instance()
        nam.setTimeout(self.REQUEST_TIMEOUT_MS)

        # Disable retries so a single timeout surfaces immediately.
        # setMaxRetry() is thread-local and was added in QGIS 3.22.
        # For older builds, temporarily override the global QgsSettings value
        # (read by the NAM retry logic on the same background thread).
        _settings_key = "/qgis/networkAndProxy/networkMaxRetries"
        _old_retries = None
        if hasattr(nam, "setMaxRetry"):
            nam.setMaxRetry(self.MAX_RETRIES)
        else:
            from qgis.core import QgsSettings

            _s = QgsSettings()
            _old_retries = _s.value(_settings_key, 3)
            _s.setValue(_settings_key, self.MAX_RETRIES)

        try:
            self._layer = QgsVectorLayer(self._uri_string, self._title, "wfs")
        finally:
            if _old_retries is not None:
                QgsSettings().setValue(_settings_key, _old_retries)

        if not self._layer.isValid():
            self._error = self._layer.error().message()
            self._layer = None
            return False

        # Transfer ownership to the main thread before finished() is called
        # there, so the layer can be safely added to QgsProject.
        self._layer.moveToThread(QgsApplication.instance().thread())
        return True

    def finished(self, result: bool):
        # finished() is always called on the main thread by the task manager.
        self.layerReady.emit(self._layer, self._error or "")
