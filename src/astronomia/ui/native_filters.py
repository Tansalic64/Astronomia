"""Filtro de eventos nativos de Windows para el menú contextual del mapa.

Ver el comentario largo de `FiltroContextMenuNativo` para el porqué de
este archivo — resumen: hace falta descartar el mensaje nativo
`WM_CONTEXTMENU` de Windows ANTES de que Qt lo procese, porque ese
procesamiento (a nivel de Qt/QtWebEngine, no de nuestro código) parece
colgar el proceso de renderizado del mapa tras un clic derecho.
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

    Historial (ver también las notas de depuración del README): tras un
    clic derecho sobre el mapa, se comprobó con eventos de ratón REALES
    (botón derecho físico del usuario, no simulados) que `mousedown` y
    `mouseup` sí llegan con normalidad al JavaScript de la página — pero
    el evento `"contextmenu"` del DOM nunca llega a sintetizarse, Y ADEMÁS
    el zoom del mapa deja de responder después, **incluso sin que nuestro
    propio código (ni JS ni Python) intervenga en absoluto** en ese clic
    derecho. Eso descarta que el problema esté en nuestro propio manejo
    del menú contextual: algo en el procesamiento INTERNO de Qt/QtWebEngine
    del mensaje nativo `WM_CONTEXTMENU` de Windows dejaba el proceso de
    renderizado de Chromium colgado.

    La solución: interceptar `WM_CONTEXTMENU` en el filtro de eventos
    nativos de la aplicación (que ve los mensajes de Windows ANTES que el
    bucle de eventos normal de Qt) y descartarlo sin más — Qt nunca
    llega a "verlo". El botón derecho (mousedown/mouseup), que sí
    funciona con normalidad, sigue llegando a Chromium igual que antes;
    solo se descarta este mensaje concreto, que es puramente el disparador
    de "quizá quieras mostrar un menú aquí", no el clic en sí. El menú
    propio del mapa se dispara entonces desde JavaScript escuchando
    `"mouseup"` (botón derecho) en vez de `"contextmenu"` — ver
    `resources/web/js/bridge.js`.
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
