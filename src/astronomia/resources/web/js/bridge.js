/*
 * Lado JavaScript del puente QWebChannel.
 *
 * Responsabilidades:
 *  1. Inicializar Aladin Lite.
 *  2. Recibir órdenes de Python (astronomiaBridge.ir_a_objeto, etc.) y
 *     aplicarlas sobre el mapa.
 *  3. Reenviar eventos del mapa (posición, clics) a Python llamando a los
 *     Slots definidos en SkyBridge (astronomia/bridge/sky_bridge.py).
 *  4. El menú contextual (clic derecho) — ver `configurarMenuContextual`.
 *
 * Historial del menú contextual (por si hay que volver a tocarlo — ha
 * costado bastante llegar hasta aquí):
 *
 * 1. Aladin Lite (vendor/aladin/aladin.js, minificado) registra SU PROPIO
 *    listener de "contextmenu" sobre su canvas y llama a
 *    `event.preventDefault()` incondicionalmente (para poder mostrar su
 *    propio menú, funcionalidad normal de Aladin activable con
 *    `showContextMenu`, aquí desactivada). Esto en sí no es el problema
 *    real (ver el punto 2), pero significa que no basta con dejar que el
 *    comportamiento por defecto del navegador ocurra.
 *
 * 2. El problema real, mucho más de fondo: el evento `"contextmenu"` del
 *    DOM **nunca llega a sintetizarse en absoluto** tras un clic derecho
 *    real (comprobado con sondas en `mousedown`/`mouseup`/`contextmenu`:
 *    los dos primeros SÍ llegan con normalidad, el último nunca) — Y,
 *    ADEMÁS, el zoom del mapa deja de responder después del clic, incluso
 *    sin que ni nuestro código ni el de Aladin lleguen a intervenir para
 *    nada (probado con un listener de "contextmenu" que jamás se disparó).
 *    Esto descarta que el problema esté aquí, en JavaScript: algo en el
 *    procesamiento INTERNO de Qt/QtWebEngine del mensaje nativo de
 *    Windows `WM_CONTEXTMENU` deja colgado el proceso de renderizado.
 *    La solución a ESE problema vive en Python
 *    (`ui/native_filters.py`): se descarta `WM_CONTEXTMENU` a nivel de
 *    filtro de eventos nativos de la aplicación, antes de que Qt llegue
 *    a procesarlo.
 *
 * 3. Con `WM_CONTEXTMENU` descartado, el DOM tampoco lo verá nunca (es
 *    quien lo sintetizaba, o lo habría sintetizado) — así que el menú no
 *    puede esperar al evento `"contextmenu"`. Se dispara en su lugar
 *    desde `"mouseup"` con `button === 2` (botón derecho), que SÍ llega
 *    con toda normalidad. Se usa fase de "captura" sobre `document` para
 *    ejecutarse antes que el propio `mouseup` interno de Aladin, y
 *    `stopPropagation()` para que el de Aladin no llegue a procesar el
 *    clic derecho como iría a hacer normalmente.
 *
 * 4. El menú en sí usa el PROPIO sistema de Aladin
 *    (`aladin.contextMenu`, un `<ul>` que Aladin ya crea siempre, esté o
 *    no activado `showContextMenu`) con nuestras propias acciones, en vez
 *    de reinventar un menú desde cero.
 */

(function () {
  "use strict";

  let aladin = null;
  let bridge = null;

  function log(mensaje) {
    if (bridge) bridge.log_js(mensaje);
    console.log("[astronomia]", mensaje);
  }

  // Aladin Lite resuelve un id de survey ("P/DSS2/color") consultando un
  // registro con VARIOS mirrors posibles, y a veces elige uno que no envía
  // cabeceras CORS (p. ej. irsa.ipac.caltech.edu) — el navegador bloquea
  // entonces la carga de teselas. Fijamos aquí explícitamente el mirror de
  // CDS/unistra (sí las envía) para no depender de qué mirror le toque.
  const MIRRORS_CDS = {
    "P/DSS2/color": "https://alasky.cds.unistra.fr/DSS/DSSColor",
    "P/2MASS/color": "https://alasky.cds.unistra.fr/2MASS/Color",
    "P/RASS": "https://alasky.cds.unistra.fr/RASS",
  };

  function crearSurvey(hipsId) {
    const url = MIRRORS_CDS[hipsId];
    return A.imageHiPS(hipsId, url ? { url } : {});
  }

  function iniciarAladin() {
    aladin = A.aladin("#aladin-lite-div", {
      survey: crearSurvey("P/DSS2/color"),
      fov: 1.5,
      projection: "SIN",
      cooFrame: "equatorial",
      showCooGrid: false,
      showReticle: true,
      showZoomControl: true,
      showFullscreenControl: true,
      showLayersControl: true,
      showGotoControl: true,
    });

    aladin.on("positionChanged", function (position) {
      if (bridge) {
        bridge.on_posicion_cambiada(position.ra, position.dec);
      }
    });

    aladin.on("objectClicked", function (objeto) {
      if (!objeto) return;
      const etiqueta = objeto.data && objeto.data.name ? objeto.data.name : "objeto";
      if (bridge) {
        bridge.on_objeto_clicado(etiqueta, objeto.ra, objeto.dec);
      }
    });

    if (window.activarTraduccionAladin) {
      window.activarTraduccionAladin("aladin-lite-div");
    }

    configurarMenuContextual();

    log("Aladin Lite inicializado");
    if (bridge) bridge.on_mapa_listo();
  }

  // Ver el comentario largo al principio del archivo para el porqué de
  // "mouseup" en vez de "contextmenu", y de la fase de captura +
  // stopPropagation.
  function configurarMenuContextual() {
    document.addEventListener(
      "mouseup",
      function (evento) {
        if (evento.button !== 2) return; // solo el botón derecho

        evento.preventDefault();
        evento.stopPropagation();

        const rect = aladin.aladinDiv.getBoundingClientRect();
        const x = evento.clientX - rect.left;
        const y = evento.clientY - rect.top;

        let coords = null;
        try {
          coords = aladin.pix2world(x, y);
        } catch (e) {
          coords = null;
        }

        const acciones = [];
        if (coords) {
          const ra = coords[0];
          const dec = coords[1];

          acciones.push({
            label: "Centrar aquí",
            action() {
              aladin.gotoRaDec(ra, dec);
            },
          });

          const textoCoords = ra.toFixed(6) + " " + dec.toFixed(6);
          acciones.push({
            label:
              "Copiar coordenadas (" + ra.toFixed(5) + "°, " + dec.toFixed(5) + "°)",
            action() {
              if (bridge) bridge.copiar_al_portapapeles(textoCoords);
            },
          });

          const coordsUrl = encodeURIComponent(textoCoords);
          acciones.push({
            label: "Ver en SIMBAD",
            action() {
              if (bridge) {
                bridge.abrir_url_externa(
                  "https://simbad.cds.unistra.fr/simbad/sim-coo?Coord=" +
                    coordsUrl +
                    "&Radius=2&Radius.unit=arcmin"
                );
              }
            },
          });
          acciones.push({
            label: "Ver en VizieR",
            action() {
              if (bridge) {
                bridge.abrir_url_externa(
                  "https://vizier.cds.unistra.fr/viz-bin/VizieR?-c=" +
                    coordsUrl +
                    "&-c.rs=120"
                );
              }
            },
          });
        } else {
          acciones.push({ label: "(fuera del mapa)", disabled: true });
        }

        aladin.contextMenu.attach(acciones, null);
        aladin.contextMenu._show({ e: evento });
      },
      true // fase de captura: se ejecuta ANTES que el listener propio de Aladin
    );
  }

  function conectarSenalesPython() {
    bridge.ir_a_objeto.connect(function (nombre) {
      log("ir_a_objeto: " + nombre);
      aladin.gotoObject(nombre);
    });

    bridge.ir_a_coordenadas.connect(function (ra, dec) {
      log("ir_a_coordenadas: " + ra + ", " + dec);
      aladin.gotoRaDec(ra, dec);
    });

    bridge.fijar_fov.connect(function (grados) {
      aladin.setFov(grados);
    });

    bridge.cambiar_survey.connect(function (hipsId) {
      log("cambiar_survey: " + hipsId);
      aladin.setImageSurvey(crearSurvey(hipsId));
    });
  }

  function iniciar() {
    new QWebChannel(qt.webChannelTransport, function (channel) {
      bridge = channel.objects.astronomiaBridge;
      conectarSenalesPython();

      if (typeof A === "undefined") {
        // aladin.js no ha llegado a cargar (red, CDN caído, etc.). No hay
        // nada que inicializar: si seguimos, "A.aladin(...)" revienta con
        // un ReferenceError que oculta la causa real.
        log("ERROR: la librería Aladin Lite (variable global 'A') no está disponible. " +
            "Revisa la conexión a internet o el CDN de aladin.cds.unistra.fr");
        return;
      }

      if (A.init) {
        A.init.then(iniciarAladin);
      } else {
        // Fallback por si la API ya estaba lista (versiones antiguas de Aladin Lite).
        iniciarAladin();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", iniciar);
})();
