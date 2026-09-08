"""Filtro de eventos nativos de Windows: descarta `WM_CONTEXTMENU`.

Ver el docstring de `FiltroContextMenuNativo` para el porqué.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter

log = logging.getLogger("astronomia.ui.native_filters")

WM_CONTEXTMENU = 0x007B


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class FiltroContextMenuNativo(QAbstractNativeEventFilter):
    """Descarta `WM_CONTEXTMENU` antes de que Qt llegue a procesarlo.

    El clic derecho, en esta app, ya no dispara ningún menú propio (ver
    `resources/web/js/bridge.js`: se investigó a fondo y se abandonó por
    un bloqueo interno de Chromium sin solución encontrada a nivel de Qt
    ni de JavaScript — el menú se dispara con Mayús + clic izquierdo en
    su lugar). Este filtro se queda de todas formas como medida
    defensiva: sin él, un clic derecho accidental del usuario deja
    colgado el proceso de renderizado del mapa (comprobado con eventos de
    ratón reales: tras el clic, hasta el zoom con la rueda deja de
    responder). Descartando `WM_CONTEXTMENU` al nivel más bajo posible —
    el filtro de eventos nativos de la aplicación, que ve los mensajes de
    Windows ANTES que el bucle de eventos normal de Qt — ese cuelgue no
    llega a producirse. El resto del clic derecho (mousedown/mouseup)
    sigue llegando con normalidad a Chromium; solo se descarta este
    mensaje concreto.
    """

    def nativeEventFilter(self, event_type: bytes, message) -> tuple[bool, int]:  # noqa: N802
        if event_type == b"windows_generic_MSG":
            msg = _MSG.from_address(int(message))
            if msg.message == WM_CONTEXTMENU:
                return True, 0
        return False, 0


def instalar_filtro_context_menu(app) -> QAbstractNativeEventFilter | None:
    """Instala el filtro si estamos en Windows; no hace nada en otros SO.

    Devuelve la instancia del filtro: HAY QUE guardar una referencia a
    ella en algún sitio que viva tanto como `app` (p. ej.
    `app._filtro_context_menu = instalar_filtro_context_menu(app)`) —
    Qt no mantiene viva la parte Python del filtro por su cuenta, y si se
    recolecta como basura, `installNativeEventFilter` deja de funcionar
    (o peor, puede crashear al intentar llamar a un objeto ya liberado).
    """
    if sys.platform != "win32":
        log.debug("Filtro de WM_CONTEXTMENU no instalado: no es Windows")
        return None
    filtro = FiltroContextMenuNativo()
    app.installNativeEventFilter(filtro)
    return filtro
