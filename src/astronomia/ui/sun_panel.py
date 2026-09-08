"""Panel lateral (QDockWidget) con imágenes solares casi en tiempo real.

Descarga asíncrona vía `QNetworkAccessManager` (nunca bloquea la UI, a
diferencia de `urllib`/`requests` llamados directamente). Para GONG, que
no tiene una URL fija de "última imagen" (a diferencia de SDO), primero
se pide el listado del directorio del día en curso (UTC) y, si todavía
no hay nada (p. ej. justo tras medianoche UTC), se reintenta con el día
anterior — ver `core/solar.py` para la parte sin Qt de esta lógica.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QEvent, Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from astronomia.core.solar import (
    FUENTES_SOLARES,
    extraer_ultima_imagen_gong,
    url_directorio_gong,
)

log = logging.getLogger("astronomia.ui.sun_panel")


class SunPanel(QDockWidget):
    """Dock con una imagen del Sol que se refresca sola según la fuente elegida."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Sol en directo", parent)
        self.setObjectName("sun_panel")

        self._manager = QNetworkAccessManager(self)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refrescar)
        self._reply: QNetworkReply | None = None
        self._reply_listado: QNetworkReply | None = None
        self._pixmap_original: QPixmap | None = None

        contenedor = QWidget(self)
        layout = QVBoxLayout(contenedor)

        self._selector = QComboBox(contenedor)
        for fuente in FUENTES_SOLARES:
            self._selector.addItem(f"{fuente.nombre} — {fuente.descripcion}", fuente.id)
        self._selector.currentIndexChanged.connect(self._on_fuente_cambiada)
        layout.addWidget(self._selector)

        self._imagen = QLabel(contenedor)
        self._imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._imagen.setMinimumSize(280, 280)
        self._imagen.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._imagen.setStyleSheet("background-color: black; color: #888;")
        self._imagen.setText("Cargando…")
        self._imagen.installEventFilter(self)
        layout.addWidget(self._imagen, stretch=1)

        fila = QHBoxLayout()
        self._estado = QLabel("", contenedor)
        fila.addWidget(self._estado, stretch=1)
        boton_actualizar = QPushButton("Actualizar ahora", contenedor)
        boton_actualizar.clicked.connect(self._refrescar)
        fila.addWidget(boton_actualizar)
        layout.addLayout(fila)

        self.setWidget(contenedor)

        # Arranca el temporizador con la cadencia de la fuente por defecto
        # y pide la primera imagen. Con un pequeño retraso, no en el propio
        # constructor: si `QNetworkAccessManager.get()` se dispara en el
        # mismo instante en que la ventana principal está montando el mapa
        # (`SkyView`), la entrada de ratón sobre el mapa (rueda, botón
        # derecho) deja de funcionar por completo, sin ningún error visible
        # — comprobado. Un respiro de medio segundo antes de la primera
        # petición de red evita la colisión.
        QTimer.singleShot(500, lambda: self._on_fuente_cambiada(0))

    # -- Fuente seleccionada -----------------------------------------------------
    def _fuente_actual(self):
        return FUENTES_SOLARES[self._selector.currentIndex()]

    def _on_fuente_cambiada(self, _index: int) -> None:
        fuente = self._fuente_actual()
        self._timer.stop()
        self._timer.start(fuente.cadencia_minutos * 60_000)
        self._pixmap_original = None
        self._imagen.setPixmap(QPixmap())
        self._imagen.setText("Cargando…")
        self._refrescar()

    # -- Descarga -------------------------------------------------------------------
    def _refrescar(self) -> None:
        fuente = self._fuente_actual()
        self._estado.setText("Actualizando…")
        if fuente.url_fija:
            self._pedir_imagen(fuente.url_fija)
        else:
            self._pedir_listado_gong(datetime.now(timezone.utc))

    def _abortar_si_en_curso(self, reply: QNetworkReply | None) -> None:
        if reply is None:
            return
        try:
            reply.abort()
        except RuntimeError:
            # El objeto C++ ya se destruyó (deleteLater de una petición
            # anterior que ya había terminado): nada que abortar.
            pass

    def _pedir_listado_gong(self, fecha: datetime, es_reintento: bool = False) -> None:
        self._abortar_si_en_curso(self._reply_listado)
        peticion = QNetworkRequest(QUrl(url_directorio_gong(fecha)))
        reply = self._manager.get(peticion)
        self._reply_listado = reply
        reply.finished.connect(
            lambda r=reply, f=fecha, reint=es_reintento: self._on_listado_gong_recibido(r, f, reint)
        )

    def _on_listado_gong_recibido(self, reply: QNetworkReply, fecha: datetime, es_reintento: bool) -> None:
        reply.deleteLater()
        self._reply_listado = None
        if reply.error() != QNetworkReply.NetworkError.NoError:
            if not es_reintento:
                # Puede que aún no haya directorio para "hoy" (justo tras
                # medianoche UTC): probar con el día anterior antes de rendirse.
                self._pedir_listado_gong(fecha - timedelta(days=1), es_reintento=True)
                return
            self._mostrar_error(f"GONG no disponible: {reply.errorString()}")
            return

        html = bytes(reply.readAll()).decode("utf-8", errors="replace")
        nombre_archivo = extraer_ultima_imagen_gong(html)
        if nombre_archivo is None:
            if not es_reintento:
                self._pedir_listado_gong(fecha - timedelta(days=1), es_reintento=True)
                return
            self._mostrar_error("GONG: no se encontró ninguna imagen reciente")
            return

        self._pedir_imagen(url_directorio_gong(fecha) + nombre_archivo)

    def _pedir_imagen(self, url: str) -> None:
        self._abortar_si_en_curso(self._reply)
        peticion = QNetworkRequest(QUrl(url))
        reply = self._manager.get(peticion)
        self._reply = reply
        reply.finished.connect(lambda r=reply: self._on_imagen_recibida(r))

    def _on_imagen_recibida(self, reply: QNetworkReply) -> None:
        reply.deleteLater()
        self._reply = None
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._mostrar_error(f"Error de red: {reply.errorString()}")
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(reply.readAll()):
            self._mostrar_error("La imagen recibida no se pudo decodificar")
            return

        self._pixmap_original = pixmap
        self._actualizar_pixmap_escalado()
        self._estado.setText(f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")

    def _mostrar_error(self, mensaje: str) -> None:
        log.warning(mensaje)
        self._estado.setText(mensaje)

    # -- Escalado al redimensionar ---------------------------------------------------
    def _actualizar_pixmap_escalado(self) -> None:
        if self._pixmap_original is None:
            return
        self._imagen.setPixmap(
            self._pixmap_original.scaled(
                self._imagen.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self._imagen and event.type() == QEvent.Type.Resize:
            self._actualizar_pixmap_escalado()
        return super().eventFilter(watched, event)
