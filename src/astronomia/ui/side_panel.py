"""Panel lateral (QDockWidget) con dos pestañas: Favoritos e Historial.

Este widget solo sabe pintar listas y disparar señales de navegación; no
conoce `SkyView` ni `QWebEngineView`. Es `MainWindow` quien conecta esas
señales con el mapa. Así el panel se puede probar o reutilizar aislado.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from astronomia.core.astro import calcular_visibilidad
from astronomia.core.storage import Storage
from astronomia.core.ubicacion import Ubicacion

log = logging.getLogger("astronomia.ui.side_panel")

_ROL_NOMBRE = 1000
_ROL_RA = 1001
_ROL_DEC = 1002


class SidePanel(QDockWidget):
    """Dock con Favoritos e Historial, respaldado por `Storage` (SQLite)."""

    # (nombre, ra_o_none, dec_o_none) — si ra/dec son None, que resuelva Aladin por nombre.
    navegar_a = Signal(str, object, object)

    def __init__(self, storage: Storage, parent: QWidget | None = None) -> None:
        super().__init__("Favoritos e historial", parent)
        self.setObjectName("side_panel")
        self._storage = storage
        self._ubicacion: Ubicacion | None = None

        contenedor = QWidget(self)
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(4, 4, 4, 4)

        self._tabs = QTabWidget(contenedor)
        layout.addWidget(self._tabs)

        self._lista_favoritos = self._crear_lista()
        self._tabs.addTab(self._envolver_con_botones(
            self._lista_favoritos, "Quitar favorito", self._on_quitar_favorito
        ), "★ Favoritos")

        self._lista_historial = self._crear_lista()
        self._tabs.addTab(self._envolver_con_botones(
            self._lista_historial, "Limpiar historial", self._on_limpiar_historial
        ), "🕑 Historial")

        self.setWidget(contenedor)
        self.refrescar()

    # -- Construcción --------------------------------------------------------
    def _crear_lista(self) -> QListWidget:
        lista = QListWidget(self)
        lista.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        lista.itemDoubleClicked.connect(self._on_item_doble_click)
        return lista

    def _envolver_con_botones(self, lista: QListWidget, texto_boton: str, on_click) -> QWidget:
        widget = QWidget(self)
        v = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(lista)

        fila_botones = QHBoxLayout()
        boton = QPushButton(texto_boton, widget)
        boton.clicked.connect(on_click)
        fila_botones.addStretch()
        fila_botones.addWidget(boton)
        v.addLayout(fila_botones)
        return widget

    # -- Datos ----------------------------------------------------------------
    def fijar_ubicacion(self, ubicacion: Ubicacion | None) -> None:
        """Ubicación del observador, para mostrar qué está visible ahora.

        `None` (el valor por defecto, mientras no se detecte/fije ninguna)
        simplemente hace que no se muestre esa información — el resto del
        panel funciona igual.
        """
        self._ubicacion = ubicacion
        self.refrescar()

    def refrescar(self) -> None:
        """Vuelve a cargar ambas listas desde la base de datos."""
        self._lista_favoritos.clear()
        for fav in self._storage.listar_favoritos():
            texto = fav.nombre if not fav.descripcion else f"{fav.nombre} — {fav.descripcion}"
            texto = self._con_visibilidad(texto, fav.ra, fav.dec)
            self._lista_favoritos.addItem(self._crear_item(texto, fav.nombre, fav.ra, fav.dec))

        self._lista_historial.clear()
        for entrada in self._storage.listar_historial():
            texto = self._con_visibilidad(entrada.nombre, entrada.ra, entrada.dec)
            self._lista_historial.addItem(
                self._crear_item(texto, entrada.nombre, entrada.ra, entrada.dec)
            )

    def _con_visibilidad(self, texto: str, ra: float | None, dec: float | None) -> str:
        if self._ubicacion is None or ra is None or dec is None:
            return texto
        vis = calcular_visibilidad(ra, dec, self._ubicacion.lat, self._ubicacion.lon)
        return f"{texto}  [{vis.texto_breve()}]"

    @staticmethod
    def _crear_item(texto: str, nombre: str, ra: float | None, dec: float | None) -> QListWidgetItem:
        item = QListWidgetItem(texto)
        item.setData(_ROL_NOMBRE, nombre)
        item.setData(_ROL_RA, ra)
        item.setData(_ROL_DEC, dec)
        return item

    # -- Eventos ---------------------------------------------------------------
    def _on_item_doble_click(self, item: QListWidgetItem) -> None:
        nombre = item.data(_ROL_NOMBRE)
        ra = item.data(_ROL_RA)
        dec = item.data(_ROL_DEC)
        self.navegar_a.emit(nombre, ra, dec)

    def _on_quitar_favorito(self) -> None:
        item = self._lista_favoritos.currentItem()
        if item is None:
            return
        nombre = item.data(_ROL_NOMBRE)
        self._storage.quitar_favorito(nombre)
        self.refrescar()

    def _on_limpiar_historial(self) -> None:
        self._storage.limpiar_historial()
        self.refrescar()
