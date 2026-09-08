"""Objeto expuesto al JavaScript del mapa a través de QWebChannel.

Modelo mental (viniendo de Velneo):
  - Los `Signal` son como disparadores que la parte Python emite y el JS "escucha".
  - Los `@Slot` son métodos que el JS puede invocar directamente (como llamar a
    una función de servidor desde el cliente).

Flujo típico:
  JS (Aladin) --- usuario hace clic en el cielo --> Slot `on_objeto_clicado`
  Python --- el usuario pulsa "Ir a M42" --> Signal `ir_a_objeto` --> JS mueve el mapa
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication

log = logging.getLogger("astronomia.bridge")


class SkyBridge(QObject):
    """Contrato de comunicación con la vista web del mapa celeste."""

    # -- Señales: Python -> JavaScript -------------------------------------
    ir_a_objeto = Signal(str)                # nombre de objeto ("M31", "NGC 224")
    ir_a_coordenadas = Signal(float, float)  # RA, DEC en grados
    fijar_fov = Signal(float)                # campo de visión en grados
    cambiar_survey = Signal(str)             # id de HiPS ("P/DSS2/color", ...)

    # -- Señales: JavaScript -> Python (reemitidas para que la UI reaccione) -
    mapa_listo = Signal()
    posicion_cambiada = Signal(float, float)    # RA, DEC del centro actual
    objeto_clicado = Signal(str, float, float)  # etiqueta, RA, DEC
    pagina_web_solicitada = Signal(str)         # URL a mostrar en `ui/visor_web.py`

    # -- Slots: invocables desde JavaScript ---------------------------------
    @Slot()
    def on_mapa_listo(self) -> None:
        log.info("El mapa (Aladin Lite) ha terminado de cargar")
        self.mapa_listo.emit()

    @Slot(float, float)
    def on_posicion_cambiada(self, ra: float, dec: float) -> None:
        log.debug("Centro del mapa: RA=%.5f DEC=%.5f", ra, dec)
        self.posicion_cambiada.emit(ra, dec)

    @Slot(str, float, float)
    def on_objeto_clicado(self, etiqueta: str, ra: float, dec: float) -> None:
        log.info("Objeto seleccionado en el mapa: %s (RA=%.5f DEC=%.5f)", etiqueta, ra, dec)
        self.objeto_clicado.emit(etiqueta, ra, dec)

    @Slot(str)
    def log_js(self, mensaje: str) -> None:
        """Canal para que el JS deje trazas en el log de Python."""
        log.debug("[JS] %s", mensaje)

    @Slot(str)
    def copiar_al_portapapeles(self, texto: str) -> None:
        """Copia texto usando el portapapeles nativo de Qt.

        Se llama desde el menú contextual del mapa, hecho en JavaScript —
        ver `resources/web/js/bridge.js`.
        """
        QGuiApplication.clipboard().setText(texto)
        log.debug("Copiado al portapapeles: %s", texto)

    @Slot(str)
    def abrir_url_externa(self, url: str) -> None:
        """Abre una URL en el navegador por defecto del sistema (no en la app)."""
        log.info("Abriendo enlace externo: %s", url)
        QDesktopServices.openUrl(QUrl(url))

    @Slot(str)
    def mostrar_pagina_web(self, url: str) -> None:
        """Pide mostrar una URL en una ventana propia de la app (`ui/visor_web.py`),
        en vez de salir al navegador del sistema — usado por "Ver en SIMBAD"/
        "Ver en VizieR" del menú contextual del mapa.
        """
        self.pagina_web_solicitada.emit(url)
