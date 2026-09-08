"""Ventana "Créditos y fuentes de datos": qué organismos consulta el
programa para presentar la información (mapa, imágenes solares,
ubicación), con sus logos — varios de ellos piden explícitamente ser
citados al usar sus datos, así que además de informativo es lo correcto.

Ver `core/creditos.py` para el listado en sí (sin Qt).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from astronomia.config import ICONS_DIR
from astronomia.core.creditos import FUENTES_DATOS, FuenteDatos

log = logging.getLogger("astronomia.ui.creditos")

_ALTURA_LOGO = 56


class DialogoCreditos(QDialog):
    """Lista, con logo, de los organismos y bases de datos que consulta la app."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Créditos y fuentes de datos")
        self.resize(560, 480)

        layout = QVBoxLayout(self)

        intro = QLabel(
            "Astronomía no genera ningún dato astronómico por sí misma: se apoya "
            "por completo en los siguientes organismos, a los que pertenece el "
            "mérito (y, en varios casos, piden explícitamente ser citados).",
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        area = QScrollArea(self)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(area, stretch=1)

        contenedor = QWidget(area)
        lista = QVBoxLayout(contenedor)
        for fuente in FUENTES_DATOS:
            lista.addWidget(self._crear_fila(fuente, contenedor))
            linea = QFrame(contenedor)
            linea.setFrameShape(QFrame.Shape.HLine)
            linea.setStyleSheet("color: #444;")
            lista.addWidget(linea)
        lista.addStretch()
        area.setWidget(contenedor)

        boton_cerrar = QPushButton("Cerrar", self)
        boton_cerrar.clicked.connect(self.accept)
        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(boton_cerrar)
        layout.addLayout(fila_botones)

    def _crear_fila(self, fuente: FuenteDatos, parent: QWidget) -> QWidget:
        fila = QWidget(parent)
        h = QHBoxLayout(fila)

        logo = QLabel(fila)
        logo.setFixedSize(_ALTURA_LOGO * 2, _ALTURA_LOGO)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = self._cargar_logo(fuente.logo)
        if pixmap is not None:
            logo.setPixmap(pixmap)
        h.addWidget(logo)

        textos = QVBoxLayout()
        nombre = QLabel(f"<b>{fuente.nombre}</b>", fila)
        nombre.setWordWrap(True)
        textos.addWidget(nombre)

        descripcion = QLabel(fuente.descripcion, fila)
        descripcion.setWordWrap(True)
        textos.addWidget(descripcion)

        enlace = QLabel(f'<a href="{fuente.url}">{fuente.url}</a>', fila)
        enlace.setOpenExternalLinks(False)  # lo abrimos nosotros, ver abajo
        enlace.linkActivated.connect(lambda url: QDesktopServices.openUrl(url))
        textos.addWidget(enlace)

        h.addLayout(textos, stretch=1)
        return fila

    def _cargar_logo(self, nombre_archivo: str | None) -> QPixmap | None:
        if nombre_archivo is None:
            return None
        ruta = ICONS_DIR / "creditos" / nombre_archivo
        if not ruta.is_file():
            log.warning("Logo no encontrado: %s", ruta)
            return None
        pixmap = QPixmap(str(ruta))
        if pixmap.isNull():
            log.warning("No se pudo cargar el logo: %s", ruta)
            return None
        return pixmap.scaledToHeight(_ALTURA_LOGO, Qt.TransformationMode.SmoothTransformation)
