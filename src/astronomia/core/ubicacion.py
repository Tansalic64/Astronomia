"""Ubicación del observador: modelo de datos y parseo de la respuesta de
geolocalización por IP. Sin Qt a propósito (ver `core/solar.py` para el
porqué de este patrón) — la petición de red en sí vive en
`ui/geolocalizador.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ipwho.is: gratis sin API key, HTTPS, sin límite de peticiones publicado
# (a diferencia de ipapi.co, que en la práctica devuelve 429 "RateLimited"
# con mucha facilidad — se probó y se descartó por eso). Precisión de
# ciudad (unos pocos km), más que suficiente para saber qué hay sobre el
# horizonte.
URL_GEOLOCALIZACION_IP = "https://ipwho.is/"


@dataclass(frozen=True)
class Ubicacion:
    lat: float
    lon: float
    ciudad: str = ""
    pais: str = ""

    def etiqueta(self) -> str:
        partes = [p for p in (self.ciudad, self.pais) if p]
        return ", ".join(partes) if partes else f"{self.lat:.2f}°, {self.lon:.2f}°"


def parsear_respuesta_geolocalizacion(datos: dict[str, Any]) -> Ubicacion | None:
    """Convierte el JSON de ipwho.is en una `Ubicacion`, o `None` si no es válido.

    ipwho.is devuelve `success: false` (sin `latitude`) cuando falla —
    IP no localizable, error del servicio, etc. — en vez de un código HTTP
    de error, hay que comprobarlo explícitamente.
    """
    if not isinstance(datos, dict) or datos.get("success") is False:
        return None
    try:
        lat = float(datos["latitude"])
        lon = float(datos["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    return Ubicacion(
        lat=lat,
        lon=lon,
        ciudad=str(datos.get("city") or ""),
        pais=str(datos.get("country") or ""),
    )
