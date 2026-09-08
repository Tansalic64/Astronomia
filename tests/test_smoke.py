"""Pruebas mínimas de humo: que el proyecto arranca y los módulos base cargan."""

from astronomia.config import INDEX_HTML, settings
from astronomia.core.catalog import CATALOGO_DEMO, buscar


def test_catalogo_no_vacio():
    assert len(CATALOGO_DEMO) > 0


def test_buscar_encuentra_objeto_conocido():
    resultado = buscar("Andrómeda")
    assert resultado is not None
    assert resultado.nombre.startswith("M31")


def test_buscar_no_encuentra_devuelve_none():
    assert buscar("objeto que no existe xyz") is None


def test_settings_tiene_valores_por_defecto():
    assert settings.fov_inicial > 0
    assert settings.target_inicial


def test_index_html_existe():
    assert INDEX_HTML.is_file(), f"Falta el HTML del mapa en {INDEX_HTML}"


def test_main_window_se_crea(qtbot, tmp_path, monkeypatch):
    """Requiere pytest-qt. Verifica que la ventana principal se instancia sin errores."""
    import astronomia.config as config
    from astronomia.ui.geolocalizador import Geolocalizador
    from astronomia.ui.main_window import MainWindow

    # Nunca tocar la base de datos real del usuario desde un test.
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.sqlite3")
    # Ni hacer peticiones de red reales: con la BD vacía (sin ubicación
    # guardada), `_construir_contenido` dispararía una detección por IP de
    # verdad, cuya respuesta asíncrona podría llegar después de que este
    # test ya haya cerrado `storage` más abajo.
    monkeypatch.setattr(Geolocalizador, "detectar", lambda self: None)

    ventana = MainWindow()
    qtbot.addWidget(ventana)
    assert ventana.windowTitle().startswith("Astronomía")

    # El mapa y los paneles se crean diferidos (QTimer.singleShot(0, ...),
    # ver main_window.py): hay que dejar procesar el bucle de eventos antes
    # de tocar nada que dependa de ellos (o cerrar la BD que usan).
    qtbot.wait(50)
    assert ventana.sky_view is not None
    assert ventana.side_panel is not None
    assert ventana.sun_panel is not None

    ventana.storage.close()
