"""Punto de entrada: arranca la QApplication y muestra la ventana principal."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, Qt, QTranslator
from PySide6.QtWidgets import QApplication

from astronomia import __version__
from astronomia.config import APP_NAME, ORG_DOMAIN, ORG_NAME, settings


def _configurar_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s  %(levelname)-7s  %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _instalar_traducciones_qt(app: QApplication, log: logging.Logger) -> None:
    """Traduce los textos propios de Qt (botones OK/Cancelar, atajos
    estándar, etc.) al español usando los .qm que trae PySide6 de serie.

    Esto NO afecta a nuestros propios textos (ya están en español en el
    código) ni a los controles del mapa (Aladin Lite no tiene i18n propio).
    """
    ruta = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    locale = QLocale(QLocale.Language.Spanish, QLocale.Country.Spain)
    for nombre in ("qtbase", "qt"):
        traductor = QTranslator(app)
        if traductor.load(locale, nombre, "_", ruta):
            app.installTranslator(traductor)
        else:
            log.debug("No se encontró traducción de Qt '%s' en %s", nombre, ruta)


def main() -> int:
    _configurar_logging()
    log = logging.getLogger("astronomia")
    log.info("Iniciando %s v%s", APP_NAME, __version__)

    # Atributos que deben fijarse ANTES de crear la QApplication.
    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setOrganizationDomain(ORG_DOMAIN)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(__version__)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    if settings.devtools:
        # Puerto para inspeccionar el WebEngine desde Chrome: chrome://inspect
        import os

        os.environ.setdefault("QTWEBENGINE_REMOTE_DEBUGGING", "9222")

    app = QApplication(sys.argv)
    _instalar_traducciones_qt(app, log)

    # Import tardío: MainWindow arrastra QtWebEngine, que necesita la QApplication viva.
    from astronomia.ui.main_window import MainWindow
    from astronomia.ui.native_filters import instalar_filtro_context_menu

    # Ver `native_filters.py` para el porqué: hace falta descartar el
    # mensaje nativo WM_CONTEXTMENU antes de que Qt lo procese, o el clic
    # derecho sobre el mapa deja el renderizado del mapa colgado. Se
    # guarda la referencia en `app` porque Qt no la mantiene viva sola.
    app._filtro_context_menu = instalar_filtro_context_menu(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
