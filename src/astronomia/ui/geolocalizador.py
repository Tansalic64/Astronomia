"""Detecta la ubicación del observador por IP, de forma asíncrona.

Mismo patrón que `ui/sun_panel.py`: `QNetworkAccessManager` (nunca bloquea
la UI) en vez de `urllib`/`requests` directos. Ver `core/ubicacion.py` para
el parseo de la respuesta (sin Qt, testeable aparte).
"""

from __future__ import annotations

import json
import logging

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from astronomia.core.ubicacion import (
    URL_GEOLOCALIZACION_IP,
    Ubicacion,
    parsear_respuesta_geolocalizacion,
)

log = logging.getLogger("astronomia.ui.geolocalizador")


class Geolocalizador(QObject):
    """Pide la ubicación aproximada por IP y la reemite como señal de Qt."""

    ubicacion_detectada = Signal(Ubicacion)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None

    def cancelar(self) -> None:
        """Aborta la petición en curso, si hay alguna.

        Importante llamarlo antes de cerrar cosas de las que dependa el
        callback (p. ej. `Storage`) — si no, la respuesta puede llegar
        (con éxito o error) después de ese cierre e intentar usarlas.
        """
        if self._reply is None:
            return
        try:
            self._reply.abort()
        except RuntimeError:
            pass
        self._reply = None

    def detectar(self) -> None:
        self.cancelar()
        peticion = QNetworkRequest(QUrl(URL_GEOLOCALIZACION_IP))
        reply = self._manager.get(peticion)
        self._reply = reply
        reply.finished.connect(lambda r=reply: self._on_respuesta(r))

    def _on_respuesta(self, reply: QNetworkReply) -> None:
        reply.deleteLater()
        self._reply = None
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.error.emit(f"No se pudo detectar la ubicación: {reply.errorString()}")
            return

        try:
            datos = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            self.error.emit(f"Respuesta de geolocalización ilegible: {exc}")
            return

        ubicacion = parsear_respuesta_geolocalizacion(datos)
        if ubicacion is None:
            self.error.emit("El servicio de geolocalización no devolvió una ubicación válida")
            return

        log.info("Ubicación detectada por IP: %s", ubicacion.etiqueta())
        self.ubicacion_detectada.emit(ubicacion)
