"""Ventana secundaria: muestra una página web externa (SIMBAD, VizieR…)
dentro de la propia aplicación, en vez de abrir el navegador del sistema.

No modal — se puede seguir usando el mapa mientras está abierta — y se
reutiliza una única instancia: cada nueva consulta navega la MISMA ventana
a la nueva URL en vez de ir apilando ventanas (ver `MainWindow._mostrar_pagina_web`).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

log = logging.getLogger("astronomia.ui.visor_web")


class VisorWeb(QWidget):
    """Navegador embebido simple: URL + "abrir en el navegador" + la página."""

    def __init__(self, parent: QWidget | None = None) -> None:
        # `Qt.WindowType.Window`: ventana de nivel superior propia (con su
        # botón de cerrar, minimizar, etc.), no un widget hijo empotrado.
        super().__init__(parent, Qt.WindowType.Window)
        self.resize(1000, 750)

        self._vista = QWebEngineView(self)
        self._vista.titleChanged.connect(self._on_titulo_cambiado)
        self._vista.urlChanged.connect(self._on_url_cambiada)

        self._label_url = QLabel(self)
        self._label_url.setStyleSheet("color: #666;")
        boton_navegador = QPushButton("Abrir en el navegador", self)
        boton_navegador.setToolTip("Abrir esta misma página en el navegador del sistema")
        boton_navegador.clicked.connect(self._abrir_en_navegador)

        fila = QHBoxLayout()
        fila.addWidget(self._label_url, stretch=1)
        fila.addWidget(boton_navegador)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(fila)
        layout.addWidget(self._vista, stretch=1)

    def navegar_a(self, url: str) -> None:
        """Carga `url` (sustituyendo lo que hubiera antes) y trae la ventana al frente."""
        log.info("Mostrando en ventana embebida: %s", url)
        self._vista.setUrl(QUrl(url))
        self._label_url.setText(url)
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_titulo_cambiado(self, titulo: str) -> None:
        self.setWindowTitle(titulo or "Consulta web")

    def _on_url_cambiada(self, url: QUrl) -> None:
        self._label_url.setText(url.toString())

    def _abrir_en_navegador(self) -> None:
        QDesktopServices.openUrl(self._vista.url())
