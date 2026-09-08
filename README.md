# Astronomía

Aplicación de escritorio de astronomía. Mapa celeste interactivo (Aladin Lite)
embebido en una ventana Qt nativa, con favoritos e historial persistentes,
un panel de imágenes solares casi en tiempo real (SDO, GONG H-alpha) y
ubicación del observador (detectada por IP o manual) para saber qué está
visible por encima del horizonte ahora mismo.

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
│   │   ├── sky_view.py           # QWebEngineView + QWebChannel
│   │   ├── visor_web.py          # ventana embebida para SIMBAD/VizieR
│   │   ├── creditos.py           # ventana "Créditos y fuentes de datos"
│   │   ├── geolocalizador.py     # detecta la ubicación por IP (QNetworkAccessManager)
│   │   └── native_filters.py     # filtro de eventos nativos de Windows (ver notas)
│   ├── bridge/sky_bridge.py      # QObject expuesto al JS (señales/slots)
│   ├── core/
│   │   ├── catalog.py            # catálogo demo de objetos (sin Qt)
│   │   ├── storage.py            # favoritos/historial/ubicación en SQLite (sin Qt)
│   │   ├── solar.py              # fuentes solares SDO/GONG (sin Qt)
│   │   ├── astro.py              # RA/Dec -> altura/azimut, tiempo sidéreo (sin Qt)
│   │   ├── ubicacion.py          # modelo Ubicacion + parseo geolocalización IP (sin Qt)
│   │   └── creditos.py           # listado de fuentes de datos (sin Qt)
│   └── resources/
│       ├── icons/creditos/       # logos de CDS/NASA/NSO (vendorizados, sin red)
│       └── web/
│           ├── index.html
│           ├── js/bridge.js      # puente JS + selección de mirror HiPS
│           ├── js/i18n_aladin.js # traducción EN->ES del propio widget de Aladin
│           ├── css/app.css
│           └── vendor/aladin/    # Aladin Lite v3 vendorizado (sin CDN)
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

## Menú del mapa

**Mayús + clic izquierdo** sobre el mapa abre un menú (el propio de Aladin
Lite, con acciones nuestras — ver `resources/web/js/bridge.js`) con:

- **Centrar aquí** — mueve el mapa al punto pulsado.
- **Copiar coordenadas** — al portapapeles.
- **Ver en SIMBAD** / **Ver en VizieR** — abren la consulta correspondiente
  en una ventana propia de la app (`ui/visor_web.py`, un `QWebEngineView`
  embebido con botón "Abrir en el navegador"), no en el navegador del
  sistema. Se reutiliza la misma ventana en consultas sucesivas.

¿Por qué Mayús + clic izquierdo y no el clic derecho, la ubicación
"natural" para un menú así? Ver la sección de depuración más abajo — en
resumen, el clic derecho tiene un bloqueo interno de Chromium en este
embebido concreto que no se ha conseguido resolver, así que se optó por
un disparador que sí funciona con total fiabilidad.

## Créditos y fuentes de datos

Menú **Ayuda → Créditos y fuentes de datos…**: lista, con logo, los
organismos de los que depende la app para presentar información (CDS,
NASA/SDO, NSO/GONG, ipwho.is) — varios de ellos piden explícitamente ser
citados al usar sus datos. Listado en `core/creditos.py` (sin Qt); logos
vendorizados en `resources/icons/creditos/` (descargados una vez de las
fuentes oficiales, sin dependencia de red en cada arranque — mismo
espíritu que Aladin Lite).

## Ubicación y visibilidad

Al primer arranque, la app intenta detectar automáticamente la ubicación del
observador por IP (`ipwho.is`, sin necesidad de permisos del sistema —
precisión de ciudad, de sobra para esto). Se guarda en SQLite y no se vuelve
a pedir en arranques posteriores, salvo que se detecte o fije otra a mano
desde el menú **Ubicación**:

- **Detectar automáticamente (por IP)** — repite la detección anterior.
- **Fijar manualmente…** — introducir latitud/longitud a mano (útil si la
  detección por IP falla, o para planificar observaciones desde otro sitio).
- **Centrar mapa en el cenit** — mueve el mapa al punto justo encima de la
  cabeza del observador en este momento.

Con la ubicación fijada, el panel de **Favoritos e historial** muestra junto
a cada objeto si está visible ahora mismo (altura sobre el horizonte y punto
cardinal, o "bajo el horizonte"), refrescado automáticamente cada 5 minutos.

Los cálculos (tiempo sidéreo, altura/azimut) están en `core/astro.py`, en
Python puro, sin dependencias externas — nada de `astropy`/`skyfield`
(robustas, pero muy pesadas para lo que hace falta: saber si algo está por
encima del horizonte con precisión de menos de un grado, no astrometría de
precisión).

Esto es una primera versión deliberadamente ligera. Una vista de horizonte
completa al estilo Stellarium (constelaciones, estrellas a simple vista,
planetas, en un panel aparte) se consideró y se descartó por ahora: Aladin
Lite es un visor de cielo profundo (imágenes de survey), no un motor de
planetario — haría falta una librería nueva y datos (catálogo de estrellas,
líneas de constelaciones) que no tenemos. Queda como posible fase futura.

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

- **Menú del mapa: por qué NO es el clic derecho.** El más largo de
  depurar de todos, con diferencia. Resumen de dónde acabó la
  investigación (la historia completa, paso a paso, está en el
  comentario de cabecera de `resources/web/js/bridge.js`):
  - Confirmado con clics reales del usuario (no solo entrada sintética):
    tras soltar el botón derecho, `mousedown`/`mouseup` SÍ llegan con
    normalidad al JavaScript de la página — pero el proceso de
    **renderizado de Chromium se queda bloqueado por dentro** justo
    después: no se ejecuta ninguna tarea de JavaScript nueva (ni un
    `setTimeout` trivial disparado desde otro evento) durante más de 40
    segundos.
  - Se probaron, sin éxito, todas las vías razonables: menú en JS
    disparado por `mousedown` o por `mouseup` (en fase de captura y de
    burbuja, con y sin `stopPropagation()`), `contextMenuEvent()` de Qt,
    un `eventFilter` sobre `self.focusProxy()` (el widget interno de
    renderizado de Chromium — `QWebEngineView` es solo un envoltorio),
    confirmar la petición de Chromium con
    `lastContextMenuRequest().setAccepted(True)`, y descartar el mensaje
    nativo `WM_CONTEXTMENU` de Windows a nivel de aplicación (esto último
    SÍ arregla un problema relacionado — que hasta el zoom con la rueda
    dejara de responder tras un clic derecho — y se queda en
    `ui/native_filters.py` como medida defensiva, pero no consigue que el
    menú aparezca).
  - `self.lastContextMenuRequest()` nunca llega a rellenarse en esta app
    (con la construcción diferida de `SkyView` que hace falta para que
    el zoom funcione — ver el punto anterior), lo que apunta a que
    Chromium se queda esperando por dentro a completar la información
    del menú contextual que intenta construir automáticamente en
    cualquier clic derecho — y esa espera nunca se resuelve en este
    embebido concreto. Ninguna vía a nivel de Qt o de JavaScript consigue
    desbloquearlo.
  - **La solución**: no depender del clic derecho para nada. El botón
    IZQUIERDO ya funciona perfectamente en esta app (zoom, arrastre) —
    así que el menú se dispara con **Mayús + clic izquierdo**
    (`resources/web/js/bridge.js`, función `configurarMenu`), un simple
    `mouseup` con `shiftKey`, sin ningún rodeo. El menú en sí usa el
    PROPIO sistema de Aladin (`aladin.contextMenu`, que Aladin crea
    siempre, esté o no activado `showContextMenu`) con nuestras propias
    acciones ("Centrar aquí", "Copiar coordenadas", "Ver en SIMBAD", "Ver
    en VizieR"). Con esto, `SkyView` (`ui/sky_view.py`) no necesita
    NINGÚN código de menú: solo expone los Slots que la acción de JS
    llama directamente (`copiar_al_portapapeles`, `mostrar_pagina_web`,
    en `bridge/sky_bridge.py`).

## Empaquetado (más adelante)

Con `pyinstaller` (incluido en `[dev]`):

```powershell
pyinstaller run.py --name Astronomia --windowed --add-data "src/astronomia/resources;astronomia/resources"
```
