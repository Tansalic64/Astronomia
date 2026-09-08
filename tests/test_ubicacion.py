"""Tests del parseo de la respuesta de geolocalización por IP (sin red)."""

from astronomia.core.ubicacion import Ubicacion, parsear_respuesta_geolocalizacion

_RESPUESTA_VALIDA = {
    "success": True,
    "latitude": 40.4168,
    "longitude": -3.7038,
    "city": "Madrid",
    "country": "Spain",
}


def test_parsear_respuesta_valida():
    ubicacion = parsear_respuesta_geolocalizacion(_RESPUESTA_VALIDA)
    assert ubicacion == Ubicacion(lat=40.4168, lon=-3.7038, ciudad="Madrid", pais="Spain")


def test_parsear_respuesta_con_fallo_devuelve_none():
    assert parsear_respuesta_geolocalizacion({"success": False, "message": "IP not found"}) is None


def test_parsear_respuesta_sin_coordenadas_devuelve_none():
    assert parsear_respuesta_geolocalizacion({"city": "Madrid"}) is None


def test_parsear_respuesta_no_es_diccionario_devuelve_none():
    assert parsear_respuesta_geolocalizacion([]) is None  # type: ignore[arg-type]


def test_etiqueta_usa_ciudad_y_pais():
    ubicacion = Ubicacion(lat=1.0, lon=2.0, ciudad="Madrid", pais="Spain")
    assert ubicacion.etiqueta() == "Madrid, Spain"


def test_etiqueta_cae_a_coordenadas_si_no_hay_ciudad():
    ubicacion = Ubicacion(lat=40.4168, lon=-3.7038)
    assert ubicacion.etiqueta() == "40.42°, -3.70°"
