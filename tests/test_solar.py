"""Tests de la lógica solar (sin Qt, sin red)."""

from datetime import datetime, timezone

from astronomia.core.solar import (
    FUENTES_SOLARES,
    extraer_ultima_imagen_gong,
    url_directorio_gong,
)

_LISTADO_APACHE_EJEMPLO = """
<html><body>
<a href="20260908100822Th.jpg">20260908100822Th.jpg</a> 08-Sep-2026 10:08
<a href="20260908100922Bh.jpg">20260908100922Bh.jpg</a> 08-Sep-2026 10:09
<a href="20260908101022Th.jpg">20260908101022Th.jpg</a> 08-Sep-2026 10:10
<a href="parent.html">..</a>
</body></html>
"""


def test_fuentes_solares_no_vacias():
    assert len(FUENTES_SOLARES) >= 2


def test_sdo_tiene_url_fija_y_gong_no():
    ids = {f.id: f for f in FUENTES_SOLARES}
    assert ids["aia171"].url_fija is not None
    assert ids["gong_ha"].url_fija is None


def test_url_directorio_gong_tiene_formato_esperado():
    fecha = datetime(2026, 9, 8, tzinfo=timezone.utc)
    assert url_directorio_gong(fecha) == "https://gong2.nso.edu/HA/hag/202609/20260908/"


def test_extraer_ultima_imagen_gong_elige_la_mas_reciente():
    resultado = extraer_ultima_imagen_gong(_LISTADO_APACHE_EJEMPLO)
    assert resultado == "20260908101022Th.jpg"


def test_extraer_ultima_imagen_gong_listado_vacio():
    assert extraer_ultima_imagen_gong("<html><body>sin imágenes</body></html>") is None


def test_extraer_ultima_imagen_gong_ignora_archivos_no_reconocidos():
    html = '<a href="readme.txt">readme.txt</a><a href="20260908090000Uh.jpg">x</a>'
    assert extraer_ultima_imagen_gong(html) == "20260908090000Uh.jpg"
