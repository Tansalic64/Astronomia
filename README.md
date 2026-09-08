# Astronomía

Aplicación de escritorio de astronomía. Mapa celeste interactivo (Aladin Lite)
embebido en una ventana Qt nativa, con favoritos e historial persistentes y
un panel de imágenes solares casi en tiempo real (SDO, GONG H-alpha).

**Estrategia:** PySide6 (Qt6) + `QWebEngineView` para el mapa, comunicados por
`QWebChannel`. Un único proceso, un único lenguaje de control (Python).

## Estructura

```
Astronomia/
├── run.py                        # lanzador de conveniencia (python run.py)
├── pyproject.toml                # dependencias y metadatos del paquete
├── requirements.txt
├── scripts/setup.ps1             # crea el venv e instala todo
├── src/astronomia/
│   ├── app.py                    # arranque de la QApplication
│   ├── config.py                 # rutas, .env y ruta de la BD del usuario
│   ├── ui/
│   │   ├── main_window.py        # QMainWindow: menús, toolbar, statusbar
│   │   ├── side_panel.py         # QDockWidget: favoritos e historial
│   │   ├── sun_panel.py          # QDockWidget: Sol casi en directo (QNetworkAccessManager)
│   │   └── sky_view.py           # QWebEngineView + QWebChannel
│   ├── bridge/sky_bridge.py      # QObject expuesto al JS (señales/slots)
│   ├── core/
│   │   ├── catalog.py            # catálogo demo de objetos (sin Qt)
│   │   ├── storage.py            # favoritos/historial en SQLite (sin Qt)
│   │   └── solar.py              # fuentes solares SDO/GONG (sin Qt)
│   └── resources/web/
│       ├── index.html
│       ├── js/bridge.js          # puente JS + selección de mirror HiPS
│       ├── js/i18n_aladin.js     # traducción EN->ES del propio widget de Aladin
│       ├── css/app.css
│       └── vendor/aladin/        # Aladin Lite v3 vendorizado (sin CDN)
└── tests/
```

## Primer arranque

Requiere Python 3.10+ (instalado: 3.13).

```powershell
cd D:\Programacion\Python\Astronomia
.\scripts\setup.ps1
.\.venv\Scripts\python.exe run.py
```

O manualmente:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m astronomia
```

> La librería Aladin Lite está vendorizada en `resources/web/vendor/aladin/`
> (no depende de un CDN para arrancar). Lo que sí sigue necesitando internet,
> siempre, es descargar las imágenes del cielo (teselas HiPS) desde los
> servidores de CDS/Estrasburgo — eso es inherente a un mapa celeste online.

## Configuración

Copia `.env.example` a `.env` para ajustar el objeto inicial, el FOV o el
nivel de log:

```powershell
copy .env.example .env
```

## Favoritos e historial

El botón **★ Favorito** de la barra de herramientas marca/desmarca el objeto
actualmente centrado en el mapa. El panel lateral derecho (**Favoritos e
historial**, se puede ocultar/mostrar desde el menú Ver) permite navegar con
doble clic a cualquier entrada guardada.

Se guardan en SQLite, en `%APPDATA%\PedroCabaleiro\Astronomía\astronomia.sqlite3`
(ver `astronomia.core.storage.Storage`), independiente de la carpeta del
proyecto para que sobreviva a una reinstalación o a un empaquetado con
PyInstaller.

## Sol en directo

El panel lateral izquierdo (**Sol en directo**, también desde el menú Ver)
muestra una imagen del Sol que se refresca sola, con un selector de fuente:

- **SDO** (NASA) — AIA 171/193/304 Å y magnetograma HMI. Actualiza cada ~15 min.
  URL fija ("latest"), sin necesidad de autenticación.
- **GONG H-alpha** (NSO) — cromosfera (prominencias, filamentos). Actualiza
  cada ~1 min. No tiene URL fija: cada 6 estaciones alrededor del mundo sube
  su propia imagen, así que `core/solar.py` lista el directorio del día (UTC)
  y elige la más reciente (con reintento al día anterior si aún no hay nada,
  p. ej. justo tras medianoche UTC).

La descarga es asíncrona vía `QNetworkAccessManager` (nunca bloquea la UI).
El botón "Actualizar ahora" fuerza un refresco inmediato sin esperar a la
cadencia de la fuente.

## Idioma

Toda la interfaz propia (menús, toolbar, paneles) está en español desde el
código. Además:

- **Diálogos estándar de Qt** (botones "Aceptar"/"Cancelar", etc.): traducidos
  cargando los `.qm` oficiales que trae PySide6 (`_instalar_traducciones_qt`
  en `app.py`). Robusto, no depende de la versión de Aladin Lite.
- **Controles propios del mapa** (buscador, capas, ajustes, compartir,
  Simbad...): Aladin Lite v3 no tiene soporte de idiomas, así que
  `js/i18n_aladin.js` parchea el DOM con un diccionario EN→ES después de
  inicializar el mapa, y sigue vigilando con un `MutationObserver` los
  paneles que solo se crean al interactuar (capas, ajustes, HiPS browser...).
  Es **best effort**: el diccionario solo traduce coincidencias EXACTAS
  (nunca toca coordenadas, nombres de objetos ni valores de FOV, que son
  contenido dinámico), y deliberadamente NO traduce identificadores técnicos
  que no son texto de interfaz (palabras clave FITS/WCS como `RA---`,
  campos de metadatos VO/IVOA, IDs de catálogos HiPS, códigos de
  clasificación de objetos). Si una futura versión de Aladin Lite cambia
  estos textos literales, simplemente dejan de traducirse — no rompe nada.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Puente Python ↔ JavaScript

`SkyBridge` (en `bridge/sky_bridge.py`) es el contrato de comunicación:

- **Python → JS**: señales como `ir_a_objeto`, `ir_a_coordenadas`, `fijar_fov`,
  `cambiar_survey`. `bridge.js` las escucha y llama a la API de Aladin Lite.
- **JS → Python**: `bridge.js` invoca los `@Slot` (`on_mapa_listo`,
  `on_posicion_cambiada`, `on_objeto_clicado`), que `SkyBridge` reemite como
  señales de Qt para que `MainWindow` reaccione (barra de estado, historial...).

### Notas de depuración que costó descubrir

- `QWebEngineView` bloquea por defecto que una página `file://` pida recursos
  remotos (`LocalContentCanAccessRemoteUrls`, activado en `sky_view.py`).
  Sin esto, `aladin.js` (o las teselas del cielo) no llegan ni a intentar la
  conexión.
- Aladin Lite resuelve un id de survey (`"P/DSS2/color"`) contra un registro
  con varios mirrors posibles, y alguno (p. ej. `irsa.ipac.caltech.edu`) no
  envía cabeceras CORS: el navegador bloquea la carga. `bridge.js` fija
  explícitamente el mirror de `alasky.cds.unistra.fr` (sí las envía) vía
  `A.imageHiPS(id, {url: ...})` en vez de dejar que se elija uno al azar.
- `aladin.gotoRaDec(...)` anima la transición; si se fija el FOV en el mismo
  instante, la animación lo pisa al terminar — por eso `_on_mapa_listo` en
  `main_window.py` aplica el FOV inicial con un pequeño `QTimer.singleShot`.
- `QNetworkReply.deleteLater()` no borra el objeto C++ al instante. Si se
  guarda la respuesta en `self._reply` y una petición posterior intenta
  `.abort()` sobre esa referencia ya "zombi", PySide6 lanza `RuntimeError:
  Internal C++ object already deleted`. `sun_panel.py` limpia la referencia
  a `None` en el propio callback de `finished` para evitarlo.
- **La rueda del ratón (zoom) y el arrastre sobre el mapa dejan de
  funcionar por completo** (sin ningún error) si `SkyView` se añade a la
  ventana de una manera concreta. Se aisló con eventos de ratón reales
  (no simulados a nivel de Qt, que dieron falsos positivos) probando cada
  variante por separado. Hacen falta las TRES cosas a la vez:
  1. Crear `SkyView` y los `QDockWidget` (`SidePanel`, `SunPanel`) DESPUÉS
     de `window.show()`, no en el constructor de `MainWindow` — de ahí el
     `QTimer.singleShot(0, self._construir_contenido)`. La simple
     PRESENCIA de un `QDockWidget` en la ventana, se añada cuando se añada,
     ya rompe el mapa si éste se creó antes de mostrarse la ventana.
  2. NO poner `SkyView` como widget central directamente: envolverlo en un
     `QWidget` contenedor con un `QVBoxLayout` (ver `_construir_contenido`).
  3. No lanzar la primera petición de red de `SunPanel`
     (`QNetworkAccessManager.get()`) en el mismo instante en que se está
     montando `SkyView` — de ahí el `QTimer.singleShot(500, ...)` en
     `sun_panel.py` antes de la primera descarga.

- **Menú contextual (clic derecho) sobre el mapa.** El más largo de
  depurar de todos, porque durante mucho tiempo se buscó la causa en el
  sitio equivocado (routing de eventos de Qt) cuando en realidad estaba
  en JavaScript. Varios intentos fallidos, por este orden, antes de dar
  con la causa real:
  1. Un menú hecho en JS (disparado por `mousedown`) parecía dejar de
     recibir cualquier evento después del clic (`mousemove`, teclado...).
  2. Sobrescribir `contextMenuEvent()` en `SkyView`: nunca se llamaba.
  3. Instalar un `eventFilter` sobre `self.focusProxy()` (el widget
     interno de renderizado de Chromium, que es quien de verdad recibe el
     evento crudo del sistema operativo — `QWebEngineView` es solo un
     envoltorio): esto sí capturaba un `QEvent.Type.ContextMenu`, pero
     `self.lastContextMenuRequest()` se quedaba en `None` para siempre
     (con reintentos de hasta 2s), y cualquier `runJavaScript()`
     posterior también se quedaba colgado.
  4. **La causa real**, encontrada mirando el código de la propia Aladin
     Lite vendorizada (`resources/web/vendor/aladin/aladin.js`, minificado):
     registra SU PROPIO listener de `"contextmenu"` sobre su canvas y
     llama a `event.preventDefault()` **incondicionalmente** (para poder
     mostrar su propio menú, funcionalidad normal de Aladin activable con
     `showContextMenu`, que aquí tenemos desactivada). Ese
     `preventDefault()` es justo lo que le dice a Chromium "la página ya
     se ha encargado de este clic" — el proceso de render NUNCA llega a
     pedirle a Qt que muestre un menú nativo, así que
     `contextMenuEvent()`/`lastContextMenuRequest()` no se disparan
     JAMÁS. No era un error nuestro, ni de Qt, ni del entorno: es el
     comportamiento normal de un navegador ante una página que gestiona
     su propio clic derecho — simplemente había que mirar qué hacía la
     librería vendorizada en vez de pelear contra el sistema de eventos
     de Qt.
  5. **La solución**, íntegramente en `resources/web/js/bridge.js`
     (función `configurarMenuContextual`): en vez de pelear contra
     Aladin, usar su PROPIO sistema de menú contextual
     (`aladin.contextMenu`, que Aladin crea siempre, esté o no activado
     `showContextMenu`) con nuestras propias acciones ("Centrar aquí",
     "Copiar coordenadas", "Ver en SIMBAD", "Ver en VizieR"). Para eso
     hace falta interceptar el evento `"contextmenu"` ANTES que el
     listener propio de Aladin (que se re-adjunta sus acciones por
     defecto en cada clic, sobrescribiendo las nuestras): un listener en
     fase de **captura** sobre `document` se ejecuta antes que cualquier
     listener en fase de "burbuja" sobre el canvas (aunque esté en el
     mismo elemento), y `stopPropagation()` impide que el de Aladin
     llegue a ejecutarse después. Con esto, `SkyView` (`ui/sky_view.py`)
     no necesita NINGÚN código de menú contextual: solo expone los Slots
     que la acción de JS llama directamente (`copiar_al_portapapeles`,
     `abrir_url_externa`, en `bridge/sky_bridge.py`).
  6. **Verificación**: confirmado con clics reales del usuario en su
     propio PC (no solo con entrada sintética en el entorno de
     desarrollo) — el log mostraba `lastContextMenuRequest` en `None`
     indefinidamente con el enfoque anterior, confirmando que el bloqueo
     era real y no un artefacto de la sandbox de desarrollo.

## Empaquetado (más adelante)

Con `pyinstaller` (incluido en `[dev]`):

```powershell
pyinstaller run.py --name Astronomia --windowed --add-data "src/astronomia/resources;astronomia/resources"
```
