"""Configuración central: rutas del proyecto y lectura de variables de entorno.

Mantener aquí todo lo que dependa de "dónde está instalada la app" evita
rutas relativas frágiles y facilita el empaquetado con PyInstaller.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "Astronomía"
ORG_NAME = "PedroCabaleiro"
ORG_DOMAIN = "astronomia.local"


def _base_dir() -> Path:
    """Carpeta raíz de recursos.

    - En desarrollo: la carpeta del paquete `astronomia`.
    - Empaquetado con PyInstaller: la carpeta temporal `_MEIPASS`.
    """
    if getattr(sys, "frozen", False):  # ejecutable PyInstaller
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


BASE_DIR: Path = _base_dir()
RESOURCES_DIR: Path = BASE_DIR / "resources"
WEB_DIR: Path = RESOURCES_DIR / "web"
ICONS_DIR: Path = RESOURCES_DIR / "icons"
INDEX_HTML: Path = WEB_DIR / "index.html"


def _data_dir() -> Path:
    """Carpeta de datos del usuario (favoritos, historial, config futura).

    Deliberadamente separada de BASE_DIR: BASE_DIR puede vivir dentro de un
    .exe empaquetado (de solo lectura), así que los datos del usuario van a
    %APPDATA%\\<Organización>\\<App> (estándar en Windows), igual que haría
    QStandardPaths.AppDataLocation sin necesitar Qt aquí.
    """
    appdata = os.environ.get("APPDATA")
    raiz = Path(appdata) if appdata else Path.home() / ".astronomia"
    return raiz / ORG_NAME / APP_NAME


DATA_DIR: Path = _data_dir()
DB_PATH: Path = DATA_DIR / "astronomia.sqlite3"


def _load_dotenv() -> None:
    """Carga un archivo .env sencillo (KEY=VALUE) si existe, sin dependencias."""
    # Buscar .env junto al proyecto (dev) o junto al ejecutable (empaquetado).
    candidates = [Path.cwd() / ".env", BASE_DIR.parent.parent.parent / ".env"]
    for env_path in candidates:
        if not env_path.is_file():
            continue
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
        break


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Ajustes de arranque, resueltos desde variables de entorno."""

    log_level: str = os.environ.get("ASTRONOMIA_LOG_LEVEL", "INFO").upper()
    devtools: bool = os.environ.get("ASTRONOMIA_DEVTOOLS", "0") == "1"
    target_inicial: str = os.environ.get("ASTRONOMIA_TARGET_INICIAL", "M31")
    fov_inicial: float = float(os.environ.get("ASTRONOMIA_FOV_INICIAL", "1.5"))


settings = Settings()
