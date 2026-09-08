"""Ventana principal: menús, barra de herramientas, barra de estado y el mapa.

Comparación con Velneo para orientarte:
  - QMainWindow          ~ la ventana de proceso con su barra de menú/herramientas
  - QAction               ~ una opción de menú/botón de barra de herramientas
  - Signal/Slot (connect) ~ evento -> disparador
  - QStatusBar            ~ la línea de estado inferior
  - QDockWidget           ~ un panel acoplable (como una subventana anclada)
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from astronomia import __version__
from astronomia.config import APP_NAME, settings
from astronomia.core.astro import cenit_ra_dec
from astronomia.core.catalog import CATALOGO_DEMO, buscar
from astronomia.core.storage import Storage
from astronomia.core.ubicacion import Ubicacion
from astronomia.ui.creditos import DialogoCreditos
from astronomia.ui.geolocalizador import Geolocalizador
from astronomia.ui.side_panel import SidePanel
from astronomia.ui.sky_view import SkyView
from astronomia.ui.sun_panel import SunPanel
from astronomia.ui.visor_web import VisorWeb

log = logging.getLogger("astronomia.ui.main_window")

SURVEYS = {
    "Óptico (DSS2 color)": "P/DSS2/color",
    "Infrarrojo (2MASS color)": "P/2MASS/color",
    "Rayos X (ROSAT)": "P/RASS",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.resize(1200, 800)

        # Objeto/posición actualmente centrados en el mapa (para el botón
        # de favorito y para registrar el historial). `None` mientras no
        # se sepa aún (p. ej. justo tras pedirle a Aladin que resuelva un
        # nombre por Simbad, antes de que llegue `posicion_cambiada`).
        self._objeto_actual: str | None = None
        self._pos_actual: tuple[float, float] | None = None
        self._ubicacion: Ubicacion | None = None
        # Ventana embebida para "Ver en SIMBAD"/"Ver en VizieR" — se crea la
        # primera vez que hace falta (ver `_on_pagina_web_solicitada`), no aquí.
        self._visor_web: VisorWeb | None = None

        self.storage = Storage()

        self._geolocalizador = Geolocalizador(self)
        self._geolocalizador.ubicacion_detectada.connect(self._on_ubicacion_detectada)
        self._geolocalizador.error.connect(self._on_error_ubicacion)

        self._crear_barra_herramientas()
        self._menu_ver = self._crear_menus()
        self._crear_menu_ubicacion()
        self._crear_barra_estado()

        # El mapa y los paneles acoplables se crean DESPUÉS de mostrar la
        # ventana, no aquí. Ver `_construir_contenido` para el motivo.
        QTimer.singleShot(0, self._construir_contenido)

    # -- Construcción de la UI ----------------------------------------------
    def _construir_contenido(self) -> None:
        """Crea el mapa (`SkyView`) y los paneles acoplables, y los engancha
        a la ventana.

        Se dispara vía `QTimer.singleShot(0, ...)` desde `__init__` (no se
        crea nada de esto ahí directamente) por un motivo muy concreto,
        comprobado con eventos de ratón reales, no solo en teoría: en
        `QMainWindow`, la simple PRESENCIA de un `QDockWidget` (da igual
        cuándo se añada) hace que la rueda del ratón (zoom) y el botón
        derecho (menú contextual) del mapa dejen de funcionar por
        completo, sin ningún error visible — el mapa se ve y renderiza
        perfectamente, pero deja de recibir esos eventos. Dos cosas juntas
        lo arreglan (una sola no basta, se comprobó por separado):
          1. Crear `SkyView` — y los `QDockWidget` — DESPUÉS de que la
             ventana se haya mostrado por primera vez (de ahí el
             `singleShot(0, ...)`, que se dispara en la primera vuelta del
             bucle de eventos, siempre después de `window.show()` — ver
             `app.py`).
          2. NO poner `SkyView` como widget central directamente: envolverlo
             en un `QWidget` contenedor sencillo con un `QVBoxLayout`.
        """
        self.sky_view = SkyView(self)
        contenedor = QWidget(self)
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sky_view)
        self.setCentralWidget(contenedor)
        self._conectar_senales()

        self.side_panel = SidePanel(self.storage, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.side_panel)
        self.side_panel.navegar_a.connect(self._navegar_a)
        self._menu_ver.addAction(self.side_panel.toggleViewAction())

        self.sun_panel = SunPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sun_panel)
        self._menu_ver.addAction(self.sun_panel.toggleViewAction())

        # Ubicación: si ya se conocía de una sesión anterior, se usa
        # directamente; si no, se intenta detectar por IP en segundo
        # plano (no bloquea nada si falla o tarda — el resto de la app
        # funciona igual sin ubicación, simplemente sin el indicador de
        # "visible ahora").
        ubicacion_guardada = self.storage.obtener_ubicacion()
        if ubicacion_guardada is not None:
            self._fijar_ubicacion(ubicacion_guardada, guardar=False)
        else:
            self._geolocalizador.detectar()

        # Refresca periódicamente el indicador de "visible ahora" del
        # panel lateral (la altura de un objeto cambia con el tiempo,
        # aunque el usuario no toque nada).
        self._timer_refresco_visibilidad = QTimer(self)
        self._timer_refresco_visibilidad.timeout.connect(self.side_panel.refrescar)
        self._timer_refresco_visibilidad.start(5 * 60_000)

    def _crear_barra_herramientas(self) -> None:
        barra = QToolBar("Navegación", self)
        barra.setMovable(False)
        self.addToolBar(barra)

        self.buscador = QLineEdit(self)
        self.buscador.setPlaceholderText("Buscar objeto (p. ej. M31)…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setMaximumWidth(280)
        self.buscador.returnPressed.connect(self._on_buscar)
        barra.addWidget(self.buscador)

        accion_buscar = QAction("Ir", self)
        accion_buscar.triggered.connect(self._on_buscar)
        barra.addAction(accion_buscar)

        barra.addSeparator()

        self.accion_favorito = QAction("★ Favorito", self)
        self.accion_favorito.setCheckable(True)
        self.accion_favorito.setEnabled(False)
        self.accion_favorito.setToolTip("Añadir/quitar el objeto actual de favoritos")
        self.accion_favorito.toggled.connect(self._on_toggle_favorito)
        barra.addAction(self.accion_favorito)

        barra.addSeparator()

        self.selector_survey = QComboBox(self)
        self.selector_survey.addItems(SURVEYS.keys())
        self.selector_survey.currentTextChanged.connect(self._on_survey_cambiado)
        barra.addWidget(self.selector_survey)

    def _crear_menus(self) -> QMenu:
        menu_archivo = self.menuBar().addMenu("&Archivo")

        accion_salir = QAction("&Salir", self)
        accion_salir.setShortcut(QKeySequence.StandardKey.Quit)
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

        menu_ver = self.menuBar().addMenu("&Ver")
        accion_fov = QAction("Fijar campo de visión…", self)
        accion_fov.triggered.connect(self._on_fijar_fov)
        menu_ver.addAction(accion_fov)
        # Las acciones de mostrar/ocultar los paneles se añaden más tarde,
        # desde `_construir_contenido`, cuando esos paneles ya existen.

        menu_objetos = self.menuBar().addMenu("&Objetos")
        for obj in CATALOGO_DEMO:
            accion = QAction(obj.nombre, self)
            accion.triggered.connect(
                lambda checked=False, o=obj: self._navegar_a(o.nombre, o.ra, o.dec)
            )
            menu_objetos.addAction(accion)

        menu_ayuda = self.menuBar().addMenu("A&yuda")
        accion_creditos = QAction("Créditos y fuentes de datos…", self)
        accion_creditos.triggered.connect(self._on_creditos)
        menu_ayuda.addAction(accion_creditos)
        accion_acerca = QAction("Acerca de…", self)
        accion_acerca.triggered.connect(self._on_acerca_de)
        menu_ayuda.addAction(accion_acerca)

        return menu_ver

    def _crear_barra_estado(self) -> None:
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Cargando mapa celeste…")
        self._label_ubicacion = QLabel("Ubicación: detectando…", self)
        self.statusBar().addPermanentWidget(self._label_ubicacion)

    def _crear_menu_ubicacion(self) -> None:
        menu = self.menuBar().addMenu("&Ubicación")

        accion_detectar = QAction("Detectar automáticamente (por IP)", self)
        accion_detectar.triggered.connect(self._geolocalizador.detectar)
        menu.addAction(accion_detectar)

        accion_manual = QAction("Fijar manualmente…", self)
        accion_manual.triggered.connect(self._on_fijar_ubicacion_manual)
        menu.addAction(accion_manual)

        menu.addSeparator()

        self._accion_centrar_cenit = QAction("Centrar mapa en el cenit", self)
        self._accion_centrar_cenit.setToolTip(
            "Mueve el mapa al punto justo encima de tu cabeza ahora mismo"
        )
        self._accion_centrar_cenit.setEnabled(False)  # hasta que haya ubicación
        self._accion_centrar_cenit.triggered.connect(self._on_centrar_cenit)
        menu.addAction(self._accion_centrar_cenit)

    def _conectar_senales(self) -> None:
        bridge = self.sky_view.bridge
        bridge.mapa_listo.connect(self._on_mapa_listo)
        bridge.posicion_cambiada.connect(self._on_posicion_cambiada)
        bridge.objeto_clicado.connect(self._on_objeto_clicado)
        bridge.pagina_web_solicitada.connect(self._on_pagina_web_solicitada)

    # -- Manejadores de eventos ----------------------------------------------
    def _on_mapa_listo(self) -> None:
        self.statusBar().showMessage("Mapa listo", 3000)
        self._navegar_a(settings.target_inicial)
        # `gotoRaDec` hace una transición animada; si se fija el FOV en el
        # mismo instante, la animación lo pisa al terminar. Un pequeño
        # retraso deja que la transición inicial asiente antes de aplicarlo.
        QTimer.singleShot(300, lambda: self.sky_view.fijar_fov(settings.fov_inicial))

    def _on_posicion_cambiada(self, ra: float, dec: float) -> None:
        self._pos_actual = (ra, dec)
        self.statusBar().showMessage(f"RA {ra:.4f}°   DEC {dec:.4f}°")

    def _on_objeto_clicado(self, etiqueta: str, ra: float, dec: float) -> None:
        self.statusBar().showMessage(f"Seleccionado: {etiqueta} (RA {ra:.4f}°, DEC {dec:.4f}°)", 5000)

    def _on_pagina_web_solicitada(self, url: str) -> None:
        """"Ver en SIMBAD"/"Ver en VizieR" del menú contextual del mapa:
        mostrar la página en una ventana propia en vez de salir al
        navegador del sistema. Se reutiliza la misma ventana en consultas
        sucesivas (se crea la primera vez que hace falta).
        """
        if self._visor_web is None:
            self._visor_web = VisorWeb(self)
        self._visor_web.navegar_a(url)

    def _on_buscar(self) -> None:
        texto = self.buscador.text().strip()
        if not texto:
            return
        self._navegar_a(texto)

    def _navegar_a(self, nombre: str, ra: float | None = None, dec: float | None = None) -> None:
        """Punto único de navegación: mueve el mapa, registra historial y
        actualiza el estado del botón de favorito. Lo usan el buscador, el
        menú Objetos, el panel de favoritos/historial y el arranque inicial.
        """
        if ra is None or dec is None:
            objeto_local = buscar(nombre)
            if objeto_local:
                ra, dec = objeto_local.ra, objeto_local.dec

        if ra is not None and dec is not None:
            self.sky_view.ir_a_coordenadas(ra, dec)
            self._pos_actual = (ra, dec)
        else:
            # Sin coordenadas conocidas: que lo resuelva Aladin/Simbad.
            self.sky_view.ir_a(nombre)
            self._pos_actual = None

        self._objeto_actual = nombre
        self.statusBar().showMessage(f"Navegando a: {nombre}…")

        self.storage.registrar_visita(nombre, ra, dec)
        self.side_panel.refrescar()
        self._actualizar_boton_favorito()

    def _actualizar_boton_favorito(self) -> None:
        es_fav = bool(self._objeto_actual) and self.storage.es_favorito(self._objeto_actual)
        self.accion_favorito.setEnabled(self._objeto_actual is not None)
        self.accion_favorito.blockSignals(True)
        self.accion_favorito.setChecked(es_fav)
        self.accion_favorito.blockSignals(False)

    def _on_toggle_favorito(self, marcado: bool) -> None:
        if self._objeto_actual is None:
            return

        if marcado:
            if self._pos_actual is None:
                self.statusBar().showMessage(
                    "Espera a que se resuelva la posición antes de marcar como favorito", 4000
                )
                self.accion_favorito.blockSignals(True)
                self.accion_favorito.setChecked(False)
                self.accion_favorito.blockSignals(False)
                return
            ra, dec = self._pos_actual
            self.storage.anadir_favorito(self._objeto_actual, ra, dec)
        else:
            self.storage.quitar_favorito(self._objeto_actual)

        self.side_panel.refrescar()

    def _on_survey_cambiado(self, etiqueta: str) -> None:
        hips_id = SURVEYS.get(etiqueta)
        if hips_id:
            self.sky_view.cambiar_survey(hips_id)

    def _on_fijar_fov(self) -> None:
        valor, ok = QInputDialog.getDouble(
            self, "Campo de visión", "Grados:", 1.5, 0.0001, 180.0, 4
        )
        if ok:
            self.sky_view.fijar_fov(valor)

    def _on_creditos(self) -> None:
        DialogoCreditos(self).exec()

    def _on_acerca_de(self) -> None:
        QMessageBox.about(
            self,
            f"Acerca de {APP_NAME}",
            f"{APP_NAME} v{__version__}\n\n"
            "Mapa celeste con Aladin Lite embebido vía QWebEngineView.\n"
            "Estrategia: PySide6 + QWebChannel.",
        )

    # -- Ubicación del observador ------------------------------------------
    def _on_ubicacion_detectada(self, ubicacion: Ubicacion) -> None:
        self._fijar_ubicacion(ubicacion, guardar=True)
        self.statusBar().showMessage(f"Ubicación detectada: {ubicacion.etiqueta()}", 4000)

    def _on_error_ubicacion(self, mensaje: str) -> None:
        log.warning(mensaje)
        # No es un error grave: el resto de la app funciona igual sin
        # ubicación. Un aviso breve en la barra de estado basta — no hace
        # falta interrumpir al usuario con un diálogo modal.
        self.statusBar().showMessage(mensaje, 5000)
        if self._ubicacion is None:
            self._label_ubicacion.setText("Ubicación: no disponible")

    def _fijar_ubicacion(self, ubicacion: Ubicacion, guardar: bool) -> None:
        self._ubicacion = ubicacion
        if guardar:
            self.storage.guardar_ubicacion(ubicacion)
        self._label_ubicacion.setText(f"📍 {ubicacion.etiqueta()}")
        self._accion_centrar_cenit.setEnabled(True)
        # El panel lateral puede no existir todavía (se llama también desde
        # `_construir_contenido`, justo después de crearlo — pero por si
        # este método se llama alguna vez antes, mejor no asumir).
        panel = getattr(self, "side_panel", None)
        if panel is not None:
            panel.fijar_ubicacion(ubicacion)

    def _on_fijar_ubicacion_manual(self) -> None:
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Fijar ubicación manualmente")
        formulario = QFormLayout(dialogo)

        actual = self._ubicacion
        campo_lat = QDoubleSpinBox(dialogo)
        campo_lat.setRange(-90.0, 90.0)
        campo_lat.setDecimals(4)
        campo_lat.setSuffix("°")
        campo_lat.setValue(actual.lat if actual else 0.0)
        formulario.addRow("Latitud (N positiva):", campo_lat)

        campo_lon = QDoubleSpinBox(dialogo)
        campo_lon.setRange(-180.0, 180.0)
        campo_lon.setDecimals(4)
        campo_lon.setSuffix("°")
        campo_lon.setValue(actual.lon if actual else 0.0)
        formulario.addRow("Longitud (E positiva):", campo_lon)

        campo_ciudad = QLineEdit(dialogo)
        campo_ciudad.setText(actual.ciudad if actual else "")
        campo_ciudad.setPlaceholderText("Opcional")
        formulario.addRow("Nombre (opcional):", campo_ciudad)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialogo
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        formulario.addRow(botones)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            ubicacion = Ubicacion(lat=campo_lat.value(), lon=campo_lon.value(), ciudad=campo_ciudad.text().strip())
            self._fijar_ubicacion(ubicacion, guardar=True)

    def _on_centrar_cenit(self) -> None:
        if self._ubicacion is None:
            return
        ra, dec = cenit_ra_dec(self._ubicacion.lat, self._ubicacion.lon)
        self.sky_view.ir_a_coordenadas(ra, dec)
        self.statusBar().showMessage("Mapa centrado en el cenit", 3000)

    # -- Ciclo de vida ---------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        # Antes de cerrar la BD: si hay una detección de ubicación en
        # curso, su respuesta podría llegar después y usarla ya cerrada.
        self._geolocalizador.cancelar()
        self.storage.close()
        super().closeEvent(event)
