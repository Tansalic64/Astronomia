"""Persistencia local: favoritos e historial de objetos (SQLite).

Vive en `core/` a propósito: es lógica de dominio sin Qt, para que se pueda
probar y reutilizar (p. ej. desde una CLI o una futura API) sin arrastrar
PySide6. `MainWindow` solo la usa a través de esta clase.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from astronomia import config
from astronomia.core.ubicacion import Ubicacion

log = logging.getLogger("astronomia.core.storage")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS favoritos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    ra          REAL NOT NULL,
    dec         REAL NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    creado_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historial (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    ra           REAL,
    dec          REAL,
    visitado_en  TEXT NOT NULL
);

-- Una sola fila (id fijo = 1): la última ubicación conocida del
-- observador, detectada por IP o fijada a mano.
CREATE TABLE IF NOT EXISTS ubicacion (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    lat          REAL NOT NULL,
    lon          REAL NOT NULL,
    ciudad       TEXT NOT NULL DEFAULT '',
    pais         TEXT NOT NULL DEFAULT '',
    actualizado_en TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Favorito:
    id: int
    nombre: str
    ra: float
    dec: float
    descripcion: str
    creado_en: str


@dataclass(frozen=True)
class EntradaHistorial:
    id: int
    nombre: str
    ra: float | None
    dec: float | None
    visitado_en: str


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Storage:
    """Wrapper fino sobre sqlite3: una instancia = una conexión abierta."""

    def __init__(self, db_path: Path | None = None) -> None:
        # Resuelto en cada llamada (no como valor por defecto fijado al
        # importar el módulo) para que los tests puedan monkeypatchear
        # `astronomia.config.DB_PATH` y usar una base de datos temporal.
        db_path = Path(db_path) if db_path is not None else config.DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        log.info("Base de datos local: %s", db_path)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Storage:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # -- Favoritos -----------------------------------------------------------
    def listar_favoritos(self) -> list[Favorito]:
        filas = self._conn.execute(
            "SELECT * FROM favoritos ORDER BY nombre COLLATE NOCASE"
        ).fetchall()
        return [Favorito(**dict(fila)) for fila in filas]

    def es_favorito(self, nombre: str) -> bool:
        fila = self._conn.execute(
            "SELECT 1 FROM favoritos WHERE nombre = ?", (nombre,)
        ).fetchone()
        return fila is not None

    def anadir_favorito(self, nombre: str, ra: float, dec: float, descripcion: str = "") -> None:
        self._conn.execute(
            """
            INSERT INTO favoritos (nombre, ra, dec, descripcion, creado_en)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(nombre) DO UPDATE SET
                ra = excluded.ra,
                dec = excluded.dec,
                descripcion = excluded.descripcion
            """,
            (nombre, ra, dec, descripcion, _ahora_iso()),
        )
        self._conn.commit()
        log.info("Favorito guardado: %s", nombre)

    def quitar_favorito(self, nombre: str) -> None:
        self._conn.execute("DELETE FROM favoritos WHERE nombre = ?", (nombre,))
        self._conn.commit()
        log.info("Favorito eliminado: %s", nombre)

    # -- Historial -------------------------------------------------------------
    def registrar_visita(self, nombre: str, ra: float | None = None, dec: float | None = None) -> None:
        self._conn.execute(
            "INSERT INTO historial (nombre, ra, dec, visitado_en) VALUES (?, ?, ?, ?)",
            (nombre, ra, dec, _ahora_iso()),
        )
        self._conn.commit()
        self._purgar_historial()

    def listar_historial(self, limite: int = 30) -> list[EntradaHistorial]:
        filas = self._conn.execute(
            "SELECT * FROM historial ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
        return [EntradaHistorial(**dict(fila)) for fila in filas]

    def limpiar_historial(self) -> None:
        self._conn.execute("DELETE FROM historial")
        self._conn.commit()

    # -- Ubicación del observador ----------------------------------------------
    def guardar_ubicacion(self, ubicacion: Ubicacion) -> None:
        self._conn.execute(
            """
            INSERT INTO ubicacion (id, lat, lon, ciudad, pais, actualizado_en)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                lat = excluded.lat,
                lon = excluded.lon,
                ciudad = excluded.ciudad,
                pais = excluded.pais,
                actualizado_en = excluded.actualizado_en
            """,
            (ubicacion.lat, ubicacion.lon, ubicacion.ciudad, ubicacion.pais, _ahora_iso()),
        )
        self._conn.commit()
        log.info("Ubicación guardada: %s", ubicacion.etiqueta())

    def obtener_ubicacion(self) -> Ubicacion | None:
        fila = self._conn.execute("SELECT * FROM ubicacion WHERE id = 1").fetchone()
        if fila is None:
            return None
        return Ubicacion(lat=fila["lat"], lon=fila["lon"], ciudad=fila["ciudad"], pais=fila["pais"])

    def _purgar_historial(self, mantener: int = 200) -> None:
        """Evita que el historial crezca sin límite."""
        self._conn.execute(
            """
            DELETE FROM historial WHERE id NOT IN (
                SELECT id FROM historial ORDER BY id DESC LIMIT ?
            )
            """,
            (mantener,),
        )
        self._conn.commit()
