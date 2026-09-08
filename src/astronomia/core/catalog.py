"""Catálogo mínimo de objetos de referencia (placeholder).

Esto es a propósito muy simple: un punto de partida para que crezca con tu
propio catálogo (Messier, NGC, favoritos del usuario, etc.) sin acoplarlo
a la UI ni a Qt. `MainWindow` solo conoce esta clase a través de sus métodos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjetoCeleste:
    nombre: str
    ra: float   # ascensión recta, en grados
    dec: float  # declinación, en grados
    descripcion: str = ""


# Un puñado de objetos conocidos para probar la navegación del mapa.
CATALOGO_DEMO: list[ObjetoCeleste] = [
    ObjetoCeleste("M31 - Galaxia de Andrómeda", 10.6847, 41.2687, "Galaxia espiral vecina"),
    ObjetoCeleste("M42 - Nebulosa de Orión", 83.8221, -5.3911, "Región de formación estelar"),
    ObjetoCeleste("M45 - Las Pléyades", 56.75, 24.1167, "Cúmulo abierto"),
    ObjetoCeleste("M13 - Cúmulo de Hércules", 250.4235, 36.4613, "Cúmulo globular"),
    ObjetoCeleste("M57 - Nebulosa del Anillo", 283.3958, 33.0294, "Nebulosa planetaria"),
]


def buscar(nombre: str) -> ObjetoCeleste | None:
    """Búsqueda simple por coincidencia parcial de nombre (case-insensitive)."""
    objetivo = nombre.strip().lower()
    for obj in CATALOGO_DEMO:
        if objetivo in obj.nombre.lower():
            return obj
    return None
