"""Tests del listado de fuentes de datos (sin Qt)."""

from astronomia.config import ICONS_DIR
from astronomia.core.creditos import FUENTES_DATOS


def test_hay_al_menos_una_fuente():
    assert len(FUENTES_DATOS) > 0


def test_todas_las_fuentes_tienen_nombre_descripcion_y_url():
    for fuente in FUENTES_DATOS:
        assert fuente.nombre
        assert fuente.descripcion
        assert fuente.url.startswith("https://")


def test_los_logos_referenciados_existen_en_disco():
    for fuente in FUENTES_DATOS:
        if fuente.logo is None:
            continue
        ruta = ICONS_DIR / "creditos" / fuente.logo
        assert ruta.is_file(), f"Falta el logo de {fuente.nombre}: {ruta}"
