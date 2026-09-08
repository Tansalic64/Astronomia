/*
 * Lado JavaScript del puente QWebChannel.
 *
 * Responsabilidades:
 *  1. Inicializar Aladin Lite.
 *  2. Recibir órdenes de Python (astronomiaBridge.ir_a_objeto, etc.) y
 *     aplicarlas sobre el mapa.
 *  3. Reenviar eventos del mapa (posición, clics) a Python llamando a los
 *     Slots definidos en SkyBridge (astronomia/bridge/sky_bridge.py).
 *  4. El menú del mapa (Mayús + clic izquierdo) — ver `configurarMenu`.
 *
 * Historial del menú (por si hay que volver a tocarlo — ha costado mucho
 * llegar hasta aquí, léelo antes de "arreglar" el disparador):
 *
 * Se probó primero con el CLIC DERECHO, la ubicación "natural" para un
 * menú contextual. Tras mucho investigar (menús en JS, `contextMenuEvent`
 * de Qt, `eventFilter` sobre el widget interno de QtWebEngine,
 * `customContextMenuRequested`, confirmar la petición con
 * `setAccepted()`, bloquear el mensaje nativo `WM_CONTEXTMENU` de Windows
 * a nivel de aplicación — ver `ui/native_filters.py`, que se queda de
 * todas formas por si acaso, ver más abajo — probando también distintas
 * fases de eventos del DOM), la conclusión fue: en cuanto se suelta el
 * botón derecho, el proceso de RENDERIZADO DE CHROMIUM se queda
 * bloqueado por dentro (no un cuelgue de Qt, no un error nuestro) — dejan
 * de ejecutarse tareas de JavaScript nuevas, incluso un `setTimeout`
 * trivial disparado desde otro evento, durante más de 40 segundos
 * (probado, no son unos pocos segundos de margen). Con
 * `lastContextMenuRequest()` confirmado que JAMÁS llega a rellenarse en
 * esta app (con la construcción diferida de `SkyView` que hace falta
 * para que el zoom funcione — ver `ui/main_window.py`), todo apunta a
 * que Chromium se queda esperando por dentro a completar la información
 * del menú contextual que intenta construir automáticamente en CUALQUIER
 * clic derecho, y esa espera nunca se resuelve en este embebido concreto.
 * Ninguna de las vías probadas, a nivel de Qt o de JavaScript, consigue
 * desbloquearlo.
 *
 * La salida: no depender del botón derecho para nada. El botón IZQUIERDO
 * ya funciona perfectamente en esta app (zoom, arrastre, llevan meses
 * probados) — así que el menú se dispara con Mayús + clic izquierdo en
 * su lugar, que evita por completo ese camino roto de Chromium. Con esto,
 * ya no hace falta ninguno de los rodeos que necesitaba el clic derecho
 * (fases de captura/burbuja, `setTimeout`, confirmar la petición desde
 * Python...): un simple `mouseup` con `shiftKey` basta.
 *
 * El menú en sí sigue usando el PROPIO sistema de Aladin
 * (`aladin.contextMenu`, un `<ul>` que Aladin ya crea siempre, esté o no
 * activado `showContextMenu`) con nuestras propias acciones, en vez de
 * reinventar un menú desde cero.
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

    configurarMenu();

    log("Aladin Lite inicializado");
    if (bridge) bridge.on_mapa_listo();
  }

  // Ver el comentario largo al principio del archivo para el porqué de
  // Mayús + clic izquierdo en vez de clic derecho.
  function configurarMenu() {
    document.addEventListener("mouseup", function (evento) {
      if (evento.button !== 0 || !evento.shiftKey) return; // solo Mayús + clic izquierdo
      mostrarMenu(evento);
    });
  }

  function mostrarMenu(evento) {
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
        label: "Copiar coordenadas (" + ra.toFixed(5) + "°, " + dec.toFixed(5) + "°)",
        action() {
          if (bridge) bridge.copiar_al_portapapeles(textoCoords);
        },
      });

      const coordsUrl = encodeURIComponent(textoCoords);
      acciones.push({
        label: "Ver en SIMBAD",
        action() {
          if (bridge) {
            bridge.mostrar_pagina_web(
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
            bridge.mostrar_pagina_web(
              "https://vizier.cds.unistra.fr/viz-bin/VizieR?-c=" + coordsUrl + "&-c.rs=120"
            );
          }
        },
      });
    } else {
      acciones.push({ label: "(fuera del mapa)", disabled: true });
    }

    aladin.contextMenu.attach(acciones, null);
    aladin.contextMenu._show({ e: evento });
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
