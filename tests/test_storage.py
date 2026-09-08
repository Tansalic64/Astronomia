"""Tests del almacenamiento local (favoritos/historial), sin Qt de por medio."""

from astronomia.core.storage import Storage
from astronomia.core.ubicacion import Ubicacion


def test_favorito_se_guarda_y_se_lista(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.anadir_favorito("M31", 10.6847, 41.2687, "Galaxia de Andrómeda")

    favoritos = db.listar_favoritos()

    assert len(favoritos) == 1
    assert favoritos[0].nombre == "M31"
    assert db.es_favorito("M31") is True
    assert db.es_favorito("M42") is False


def test_anadir_favorito_existente_actualiza_en_vez_de_duplicar(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.anadir_favorito("M31", 10.0, 41.0)
    db.anadir_favorito("M31", 10.6847, 41.2687, "actualizado")

    favoritos = db.listar_favoritos()

    assert len(favoritos) == 1
    assert favoritos[0].descripcion == "actualizado"


def test_quitar_favorito(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.anadir_favorito("M42", 83.8221, -5.3911)
    db.quitar_favorito("M42")

    assert db.listar_favoritos() == []


def test_historial_registra_y_limita_orden_mas_reciente_primero(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.registrar_visita("M31", 10.6847, 41.2687)
    db.registrar_visita("M42", 83.8221, -5.3911)

    historial = db.listar_historial()

    assert [h.nombre for h in historial] == ["M42", "M31"]


def test_historial_se_purga_por_encima_del_limite(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    for i in range(5):
        db.registrar_visita(f"objeto-{i}")
    db._purgar_historial(mantener=3)

    assert len(db.listar_historial(limite=100)) == 3


def test_limpiar_historial(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.registrar_visita("M31")
    db.limpiar_historial()

    assert db.listar_historial() == []


def test_obtener_ubicacion_sin_guardar_devuelve_none(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    assert db.obtener_ubicacion() is None


def test_guardar_y_obtener_ubicacion(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.guardar_ubicacion(Ubicacion(lat=40.4168, lon=-3.7038, ciudad="Madrid", pais="Spain"))

    ubicacion = db.obtener_ubicacion()

    assert ubicacion == Ubicacion(lat=40.4168, lon=-3.7038, ciudad="Madrid", pais="Spain")


def test_guardar_ubicacion_dos_veces_actualiza_en_vez_de_duplicar(tmp_path):
    db = Storage(tmp_path / "test.sqlite3")
    db.guardar_ubicacion(Ubicacion(lat=0.0, lon=0.0, ciudad="Sitio A"))
    db.guardar_ubicacion(Ubicacion(lat=40.4168, lon=-3.7038, ciudad="Madrid"))

    ubicacion = db.obtener_ubicacion()

    assert ubicacion.ciudad == "Madrid"
