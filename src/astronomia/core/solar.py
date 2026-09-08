"""Fuentes de imágenes solares casi en tiempo real (SDO, GONG H-alpha).

Sin Qt a propósito, igual que `catalog.py` y `storage.py`: aquí solo se
construyen URLs y se resuelve "cuál es la imagen más reciente". La
descarga real (asíncrona, para no bloquear la UI) vive en `ui/sun_panel.py`.

- SDO (NASA) publica una URL fija que siempre apunta a la última imagen
  ("latest_1024_..."), actualizada cada ~15 minutos.
- GONG (NSO) NO tiene una URL fija: hay que listar el directorio del día
  y coger el fichero más reciente. Se actualiza cada ~1 minuto, repartido
  entre 6 estaciones alrededor del mundo (para cubrir las 24h).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

SDO_BASE = "https://sdo.gsfc.nasa.gov/assets/img/latest"
GONG_BASE = "https://gong2.nso.edu/HA/hag"

# Las 6 estaciones de la red GONG: Big Bear, Cerro Tololo, Learmonth,
# Mauna Loa, Teide, Udaipur. Entre todas cubren observación continua.
GONG_ESTACIONES = ["Bh", "Ch", "Lh", "Mh", "Th", "Uh"]

_RE_ARCHIVO_GONG = re.compile(
    r'href="(\d{14}(?:' + "|".join(GONG_ESTACIONES) + r')\.jpg)"'
)


@dataclass(frozen=True)
class FuenteSolar:
    id: str
    nombre: str
    descripcion: str
    cadencia_minutos: int
    # URL fija (SDO) o None si hay que resolverla en tiempo de ejecución (GONG).
    url_fija: str | None = None


FUENTES_SOLARES: list[FuenteSolar] = [
    FuenteSolar(
        "aia171", "SDO · AIA 171 Å", "Corona solar, ~600 000 K", 15,
        f"{SDO_BASE}/latest_1024_0171.jpg",
    ),
    FuenteSolar(
        "aia193", "SDO · AIA 193 Å", "Corona caliente, ~1.2 millones K", 15,
        f"{SDO_BASE}/latest_1024_0193.jpg",
    ),
    FuenteSolar(
        "aia304", "SDO · AIA 304 Å", "Cromosfera / región de transición", 15,
        f"{SDO_BASE}/latest_1024_0304.jpg",
    ),
    FuenteSolar(
        "hmib", "SDO · HMI Magnetograma", "Campo magnético fotosférico", 15,
        f"{SDO_BASE}/latest_1024_HMIB.jpg",
    ),
    FuenteSolar(
        "gong_ha", "GONG · H-alpha", "Cromosfera: prominencias y filamentos", 1,
        None,
    ),
]


def url_directorio_gong(fecha: datetime) -> str:
    """URL del listado de un día concreto (fecha en UTC) del archivo GONG."""
    return f"{GONG_BASE}/{fecha:%Y%m}/{fecha:%Y%m%d}/"


def extraer_ultima_imagen_gong(html: str) -> str | None:
    """De un listado de directorio (Apache autoindex), el .jpg más reciente
    entre las estaciones conocidas.

    El nombre de archivo empieza por AAAAMMDDhhmmss, así que el orden
    lexicográfico coincide con el orden temporal: basta un max().
    """
    archivos = _RE_ARCHIVO_GONG.findall(html)
    return max(archivos) if archivos else None
