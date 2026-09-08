"""Widget que embebe Aladin Lite en un QWebEngineView y lo conecta por QWebChannel.

Encapsula todo lo "raro" de mezclar Qt con web: cargar el HTML local, publicar
el canal en `window.astronomia` (ver resources/web/js/bridge.js) y exponer una
API en Python normal y corriente (`ir_a`, `fijar_fov`, ...) para que el resto
de la aplicación no tenga que saber que por debajo hay JavaScript.

El menú del mapa (Mayús + clic izquierdo — antes se intentó con el clic
derecho, ver `resources/web/js/bridge.js` para la historia completa) se
gestiona ENTERAMENTE en JavaScript. Por eso aquí no hay ningún código de
menú contextual: `contextMenuPolicy` se deja en `NoContextMenu` sin más,
para que un clic derecho accidental no intente mostrar el menú nativo
(roto) de Qt/Chromium — ver `ui/native_filters.py` para por qué, además,
se descarta el mensaje nativo `WM_CONTEXTMENU` de Windows.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget

from astronomia.bridge import SkyBridge
from astronomia.config import INDEX_HTML

log = logging.getLogger("astronomia.ui.sky_view")

_NIVELES_CONSOLA = {
    QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: logging.DEBUG,
    QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: logging.WARNING,
    QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: logging.ERROR,
}


class _LoggingWebEnginePage(QWebEnginePage):
    """QWebEnginePage que vuelca la consola JS (errores incluidos) al log de Python.

    Sin esto, un error de JavaScript en el mapa se ve como una línea suelta
    "js: Uncaught ReferenceError: ..." sin archivo ni número de línea, muy
    difícil de depurar. Con el override se sabe exactamente qué script y qué
    línea ha fallado.
    """

    def javaScriptConsoleMessage(self, level, message, line_number, source_id) -> None:  # noqa: N802
        nivel = _NIVELES_CONSOLA.get(level, logging.INFO)
        log.log(nivel, "[JS %s:%d] %s", source_id, line_number, message)


class SkyView(QWebEngineView):
    """Vista del mapa celeste (Aladin Lite) con puente Python<->JS ya conectado."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setPage(_LoggingWebEnginePage(self))

        # Por defecto, QtWebEngine NO deja que una página cargada desde
        # file:// (nuestro index.html) pida recursos remotos (https://).
        # Sin esto, el <script src="https://.../aladin.js"> del HTML no
        # llega ni a intentar la conexión: se bloquea antes de tocar red.
        self.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        self.page().renderProcessTerminated.connect(
            lambda status, code: log.error(
                "El proceso de renderizado del mapa ha terminado inesperadamente "
                "(estado=%s, código=%s)",
                status,
                code,
            )
        )

        self.bridge = SkyBridge()

        self._channel = QWebChannel(self.page())
        self._channel.registerObject("astronomiaBridge", self.bridge)
        self.page().setWebChannel(self._channel)

        if not INDEX_HTML.is_file():
            log.error("No se encuentra el HTML del mapa: %s", INDEX_HTML)
        self.load(QUrl.fromLocalFile(str(INDEX_HTML)))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    # -- API en Python "normal" para el resto de la aplicación -------------
    def ir_a(self, nombre_objeto: str) -> None:
        """Centra el mapa en un objeto por nombre (resuelto por Aladin/Simbad)."""
        self.bridge.ir_a_objeto.emit(nombre_objeto)

    def ir_a_coordenadas(self, ra: float, dec: float) -> None:
        """Centra el mapa en unas coordenadas ecuatoriales (grados)."""
        self.bridge.ir_a_coordenadas.emit(ra, dec)

    def fijar_fov(self, grados: float) -> None:
        """Ajusta el campo de visión (zoom) en grados."""
        self.bridge.fijar_fov.emit(grados)

    def cambiar_survey(self, hips_id: str) -> None:
        """Cambia el survey de fondo, p. ej. 'P/DSS2/color' o 'P/2MASS/color'."""
        self.bridge.cambiar_survey.emit(hips_id)
