"""Tests de la matemática de altura/azimut (sin Qt, sin red)."""

from datetime import datetime, timezone

import pytest

from astronomia.core.astro import (
    altura_azimut,
    calcular_visibilidad,
    cenit_ra_dec,
    tiempo_sideral_local_grados,
)

_MOMENTO = datetime(2026, 9, 8, 22, 30, 0, tzinfo=timezone.utc)


def test_el_cenit_tiene_altura_90_por_construccion():
    """`cenit_ra_dec` da, por definición, el punto justo encima de la
    cabeza — comprobarlo con `altura_azimut` es un test exacto (no
    depende de datos de estrellas reales), y de paso comprueba que
    ambas funciones son coherentes entre sí.
    """
    lat, lon = 40.4168, -3.7038  # Madrid
    ra, dec = cenit_ra_dec(lat, lon, _MOMENTO)

    altura, _azimut = altura_azimut(ra, dec, lat, lon, _MOMENTO)

    assert altura == pytest.approx(90.0, abs=0.01)


def test_polaris_esta_aproximadamente_a_la_altura_de_la_latitud():
    """Para un observador del hemisferio norte, la altura de Polar es
    aproximadamente igual a la latitud, sea la hora que sea (es lo que la
    hace útil para orientarse) — con margen porque no está EXACTAMENTE
    en el polo.
    """
    ra_polaris, dec_polaris = 37.9546, 89.2641
    lat = 40.0

    for momento in (
        datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 15, 15, 0, tzinfo=timezone.utc),
    ):
        altura, _azimut = altura_azimut(ra_polaris, dec_polaris, lat, 0.0, momento)
        assert abs(altura - lat) < 1.5


def test_objeto_en_el_polo_sur_celeste_no_es_visible_desde_el_norte():
    altura, _azimut = altura_azimut(0.0, -89.0, 40.0, 0.0, _MOMENTO)
    assert altura < 0


def test_tiempo_sideral_local_esta_en_rango_valido():
    lst = tiempo_sideral_local_grados(_MOMENTO, longitud_este_grados=-3.7038)
    assert 0.0 <= lst < 360.0


def test_calcular_visibilidad_objeto_visible():
    lat, lon = 40.4168, -3.7038
    ra, dec = cenit_ra_dec(lat, lon, _MOMENTO)
    vis = calcular_visibilidad(ra, dec, lat, lon, _MOMENTO)
    assert vis.visible is True
    assert "bajo el horizonte" not in vis.texto_breve()


def test_calcular_visibilidad_objeto_no_visible():
    vis = calcular_visibilidad(0.0, -89.0, 40.0, 0.0, _MOMENTO)
    assert vis.visible is False
    assert vis.texto_breve() == "bajo el horizonte"
