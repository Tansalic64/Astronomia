"""Matemática astronómica mínima: de coordenadas ecuatoriales (RA/Dec) a
coordenadas de horizonte (altura/azimut) para un observador y un instante
concretos.

Sin dependencias externas a propósito (nada de `astropy`/`skyfield`, que son
robustas pero pesan muchísimo para lo que hace falta aquí): son las fórmulas
clásicas de la astronomía de posición esférica — precisión de sobra (mejor
que un grado) para saber "¿está esto por encima del horizonte ahora mismo?",
que es todo lo que necesita el programa. Fórmulas: "Practical Astronomy with
your Calculator" (Duffett-Smith) para altura/azimut, y la expresión IAU
estándar del tiempo sidéreo medio de Greenwich.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone


def fecha_juliana(momento_utc: datetime) -> float:
    """Fecha juliana (algoritmo de Meeus, válido para el calendario gregoriano)."""
    if momento_utc.tzinfo is None:
        momento_utc = momento_utc.replace(tzinfo=timezone.utc)
    momento_utc = momento_utc.astimezone(timezone.utc)

    anio, mes = momento_utc.year, momento_utc.month
    dia = momento_utc.day + (
        momento_utc.hour + momento_utc.minute / 60 + momento_utc.second / 3600
    ) / 24
    if mes <= 2:
        anio -= 1
        mes += 12
    a = anio // 100
    b = 2 - a + a // 4
    return int(365.25 * (anio + 4716)) + int(30.6001 * (mes + 1)) + dia + b - 1524.5


def tiempo_sideral_greenwich_grados(momento_utc: datetime) -> float:
    """Tiempo sidéreo medio de Greenwich (GMST), en grados [0, 360)."""
    jd = fecha_juliana(momento_utc)
    t = (jd - 2451545.0) / 36525.0
    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * t**2
        - t**3 / 38710000
    )
    return gmst % 360.0


def tiempo_sideral_local_grados(momento_utc: datetime, longitud_este_grados: float) -> float:
    """Tiempo sidéreo local (LST), en grados [0, 360). Longitud: positiva al Este."""
    return (tiempo_sideral_greenwich_grados(momento_utc) + longitud_este_grados) % 360.0


def altura_azimut(
    ra_grados: float,
    dec_grados: float,
    lat_grados: float,
    lon_grados: float,
    momento_utc: datetime | None = None,
) -> tuple[float, float]:
    """Altura y azimut (grados) de un punto (RA/Dec) visto desde (lat/lon) ahora.

    Azimut medido desde el Norte, creciendo hacia el Este (0°=N, 90°=E,
    180°=S, 270°=O) — el convenio "de brújula" habitual, no el clásico de
    los libros de astronomía de posición (que lo miden desde el Sur).
    """
    momento_utc = momento_utc or datetime.now(timezone.utc)
    lst = tiempo_sideral_local_grados(momento_utc, lon_grados)
    ha = math.radians((lst - ra_grados) % 360.0)

    dec = math.radians(dec_grados)
    lat = math.radians(lat_grados)

    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)
    sin_alt = max(-1.0, min(1.0, sin_alt))  # errores de redondeo cerca de ±1
    alt = math.asin(sin_alt)

    cos_az = (math.sin(dec) - math.sin(alt) * math.sin(lat)) / (math.cos(alt) * math.cos(lat))
    cos_az = max(-1.0, min(1.0, cos_az))
    az = math.acos(cos_az)
    if math.sin(ha) > 0:
        az = 2 * math.pi - az

    return math.degrees(alt), math.degrees(az)


def cenit_ra_dec(
    lat_grados: float, lon_grados: float, momento_utc: datetime | None = None
) -> tuple[float, float]:
    """RA/Dec (grados) del punto justo encima de la cabeza del observador ahora."""
    momento_utc = momento_utc or datetime.now(timezone.utc)
    ra = tiempo_sideral_local_grados(momento_utc, lon_grados)
    return ra, lat_grados


@dataclass(frozen=True)
class Visibilidad:
    altura_grados: float
    azimut_grados: float

    @property
    def visible(self) -> bool:
        return self.altura_grados > 0

    def texto_breve(self) -> str:
        if not self.visible:
            return "bajo el horizonte"
        return f"↑{self.altura_grados:.0f}° ({_punto_cardinal(self.azimut_grados)})"


_PUNTOS_CARDINALES = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]


def _punto_cardinal(azimut_grados: float) -> str:
    indice = round((azimut_grados % 360) / 45) % 8
    return _PUNTOS_CARDINALES[indice]


def calcular_visibilidad(
    ra_grados: float,
    dec_grados: float,
    lat_grados: float,
    lon_grados: float,
    momento_utc: datetime | None = None,
) -> Visibilidad:
    alt, az = altura_azimut(ra_grados, dec_grados, lat_grados, lon_grados, momento_utc)
    return Visibilidad(alt, az)
