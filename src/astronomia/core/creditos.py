"""Organismos y bases de datos que consulta el programa.

Sin Qt a propósito (mismo patrón que el resto de `core/`): es solo la
lista de datos, para que la ventana de créditos (`ui/creditos.py`) no
tenga que mezclar contenido con presentación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FuenteDatos:
    nombre: str
    descripcion: str
    url: str
    logo: str | None = None  # nombre de archivo en resources/icons/creditos/, o None


FUENTES_DATOS: tuple[FuenteDatos, ...] = (
    FuenteDatos(
        nombre="CDS — Centre de Données astronomiques de Strasbourg",
        descripcion=(
            "Aladin Lite (el mapa celeste), SIMBAD y VizieR (menú del mapa), y el "
            "mirror de imágenes de survey (DSS2, 2MASS, ROSAT — originalmente de "
            "STScI/AURA, IPAC/Caltech y el Instituto Max Planck de Física "
            "Extraterrestre respectivamente)."
        ),
        url="https://cds.unistra.fr/",
        logo="cds.webp",
    ),
    FuenteDatos(
        nombre="NASA — Solar Dynamics Observatory (SDO)",
        descripcion="Imágenes solares casi en directo: AIA (171/193/304 Å) y magnetograma HMI.",
        url="https://sdo.gsfc.nasa.gov/",
        logo="nasa.svg",
    ),
    FuenteDatos(
        nombre="NSO — National Solar Observatory (GONG)",
        descripcion="Imágenes solares H-alpha casi en directo (cromosfera).",
        url="https://nso.edu/gong/",
        logo="nso.png",
    ),
    FuenteDatos(
        nombre="ipwho.is",
        descripcion="Detección de la ubicación aproximada del observador por IP.",
        url="https://ipwho.is/",
        logo=None,
    ),
)
