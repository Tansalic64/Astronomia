/*
 * Traducción al español de los textos propios de Aladin Lite (EN -> ES).
 *
 * Aladin Lite v3 no tiene soporte de idiomas: sus textos están fijos en
 * inglés dentro del bundle minificado. Esto parchea el DOM después de
 * inicializar el mapa, y sigue vigilando con un MutationObserver porque
 * varios paneles (capas, ajustes, compartir...) se crean solo cuando el
 * usuario los abre, no al arrancar.
 *
 * Es "best effort" y frágil por naturaleza: si una futura versión de
 * Aladin Lite cambia estos textos literales, dejarán de traducirse (no
 * se rompe nada, simplemente ese texto concreto vuelve a verse en inglés).
 * El diccionario solo hace coincidencia EXACTA, así que nunca toca
 * contenido dinámico (coordenadas, nombres de objetos, valores de FOV...).
 */

(function () {
  "use strict";

  // EN -> ES. Solo entradas exactas (ver nota arriba).
  //
  // Deliberadamente NO están aquí (no son texto de interfaz, son
  // identificadores técnicos — traducirlos sería incorrecto):
  //   - Palabras clave FITS/WCS: "RA---", "DEC--", "GLON-", "GLAT-"
  //   - Campos de metadatos VO/IVOA: "Char.SpatialAxis...", "Access.format"...
  //   - Constantes WebGL de mezcla: "ConstantAlpha", "SrcColor"...
  //   - IDs de catálogos/HiPS: "P/Fermi/color", "P/IRIS/color"...
  //   - Códigos de clasificación de objetos (NED): "Seyfert", "GinCl"...
  //   - Nombres propios de proyecciones que no tienen equivalente natural:
  //     "Mercator", "Mollweide", "Hammer-Aïtoff"
  const DICCIONARIO = {
    // -- Navegación / mapa ------------------------------------------------
    "A catalog, MOC or footprint": "Un catálogo, MOC o contorno",
    "Add a HiPS or an FITS image": "Añadir un HiPS o una imagen FITS",
    "Add a composite HiPS": "Añadir un HiPS compuesto",
    "Add a new HiPS": "Añadir un HiPS nuevo",
    "Add a new layer": "Añadir una capa nueva",
    "Add coverage": "Añadir cobertura",
    "Change the view projection": "Cambiar la proyección de la vista",
    "Composite HiPS": "HiPS compuesto",
    "Copy position": "Copiar posición",
    "Copy to clipboard!": "¡Copiar al portapapeles!",
    "Combine different surveys into a color one!": "¡Combina varios sondeos en uno de color!",
    "Display the coordinate grid": "Mostrar la cuadrícula de coordenadas",
    "Edit for typing an object name/position": "Editar para escribir un nombre de objeto o posición",
    "Get view URL": "Obtener la URL de la vista",
    "Grid enabled!": "¡Cuadrícula activada!",
    "HEALPix grid": "Cuadrícula HEALPix",
    "Hide the coordinate grid": "Ocultar la cuadrícula de coordenadas",
    "International Celestial Reference System": "Sistema de referencia celeste internacional",
    "Move to an interesting location": "Ir a una ubicación interesante",
    "Open the overlays menu": "Abrir el menú de superposiciones",
    "Opening menu...": "Abriendo menú…",
    "Overlays": "Superposiciones",
    "Reticle location saved!": "¡Posición de la retícula guardada!",
    "Restore original size": "Restaurar tamaño original",
    "Scroll to see more...": "Desplázate para ver más…",
    "Search for an object...": "Buscar un objeto...",
    "Settings": "Ajustes",
    "Some general settings for the": "Algunos ajustes generales para",
    "coordinate grid, the reticle or tools to enable": "la cuadrícula de coordenadas, la retícula o las herramientas a activar",
    "Spheric": "Esférica",
    "Stack": "Capas",
    "Stereographic": "Estereográfica",
    "Surveys": "Sondeos",
    "Take a snapshot": "Tomar una instantánea",
    "Tangential": "Tangencial",
    "Target interesting sky location": "Ir a una posición interesante del cielo",
    "The location you clicked on is out of the view.": "La posición en la que has hecho clic está fuera de la vista.",
    "Tools": "Herramientas",
    "Zenital equal-area": "Cenital de área igual",
    "zoom in": "acercar",
    "zoom out": "alejar",
    "Powered by Aladin Lite": "Con tecnología de Aladin Lite",

    // -- Capas / ajustes de imagen (panel de Stack) -----------------------
    "Colormap": "Mapa de color",
    "Contrast": "Contraste",
    "Cutouts": "Recortes",
    "Filter": "Filtro",
    "Enable the filter": "Activar el filtro",
    "Max cut": "Corte máximo",
    "Min cut": "Corte mínimo",
    "New catalogue layer": "Nueva capa de catálogo",
    "New image layer": "Nueva capa de imagen",
    "Opacity": "Opacidad",
    "Opacity ": "Opacidad ",
    "opacity:": "opacidad:",
    "Scale for data": "Escala de los datos",
    "Show/Hide": "Mostrar/Ocultar",
    "Stretch": "Estiramiento",
    "What name for your composite survey?": "¿Qué nombre quieres darle a tu sondeo compuesto?",

    // -- Buscador de objetos / Simbad -------------------------------------
    "Click to go to the SIMBAD database": "Haz clic para ir a la base de datos SIMBAD",
    "Could not resolve object name ": "No se pudo resolver el nombre del objeto ",
    "Declination": "Declinación",
    "More about that survey?": "¿Más sobre este sondeo?",
    "More info on the survey ?": "¿Más información sobre el sondeo?",
    "Object": "Objeto",
    "Right ascension": "Ascensión recta",
    "Simbad pointer mode, click on the icon to exit": "Modo puntero Simbad: haz clic en el icono para salir",
    "Use Sesame, our name resolver!": "¡Usa Sesame, nuestro resolvedor de nombres!",
    "Use the Simbad pointer tool!": "¡Usa la herramienta puntero de Simbad!",
    "Want to know what is a specific object ?": "¿Quieres saber qué es un objeto concreto?",

    // -- Selección / herramientas de forma ---------------------------------
    "Cone search": "Búsqueda cónica",
    "Cone search out of projection": "Búsqueda cónica fuera de la proyección",
    "Cone selection": "Selección cónica",
    "Circle out of projection. Selection canceled": "Círculo fuera de la proyección. Selección cancelada",
    "Circular": "Circular",
    "Click on this button for both layers you want to swap": "Haz clic en este botón en las dos capas que quieras intercambiar",
    "Click to add its coverage": "Haz clic para añadir su cobertura",
    "Define a selection coverage": "Definir una cobertura de selección",
    "Finish the selection": "Terminar la selección",
    "Pixel value extractor": "Extractor de valor de píxel",
    "Pixel value extractor, click on a pixel to copy it": "Extractor de valor de píxel: haz clic en un píxel para copiarlo",
    "Polygon": "Polígono",
    "Radius": "Radio",
    "Rectangular": "Rectangular",
    "Reticle": "Retícula",
    "Select sources": "Seleccionar fuentes",
    "Select the area to query the catalogue with": "Selecciona el área con la que consultar el catálogo",
    "Shape": "Forma",
    "Size of the sources": "Tamaño de las fuentes",
    "You entered the selection mode": "Has entrado en modo de selección",

    // -- Explorador de HiPS / catálogos -------------------------------------
    "Browse HiPS": "Explorar HiPS",
    "Browse a HiPS by an URL, ID or keywords": "Explora un HiPS por URL, ID o palabras clave",
    "Browse...": "Explorar...",
    "Call the cone search service": "Llamar al servicio de búsqueda cónica",
    "Catalog browser": "Explorador de catálogos",
    "Catalogue": "Catálogo",
    "Color picker": "Selector de color",
    "Download the selected tab as CSV": "Descargar la pestaña seleccionada como CSV",
    "Examples": "Ejemplos",
    "Export to notebook": "Exportar a notebook",
    "Extract the spectra under the cursor": "Extraer el espectro bajo el cursor",
    "FITS File": "Archivo FITS",
    "FITS image file": "Archivo de imagen FITS",
    "Formats availables": "Formatos disponibles",
    "From a VOTable File": "Desde un archivo VOTable",
    "From our database...": "Desde nuestra base de datos...",
    "From selection": "Desde la selección",
    "Max number of sources": "Número máximo de fuentes",
    "Mask data not in the view": "Ocultar datos fuera de la vista",
    "New catalogue layer": "Nueva capa de catálogo",
    "No WCS have been found in the image": "No se ha encontrado WCS en la imagen",
    "Open the cutout service form": "Abrir el formulario del servicio de recortes",
    "Query": "Consulta",
    "Resolution": "Resolución",
    "Resolving ": "Resolviendo ",
    "Show/hide spectra": "Mostrar/ocultar espectro",
    "Slice": "Corte",
    "Spectra": "Espectro",
    "Symbol": "Símbolo",
    "Type ID, title, keyword or URL": "Escribe ID, título, palabra clave o URL",
    "Want to filter HiPS surveys by criteria ?": "¿Quieres filtrar los sondeos HiPS por criterios?",
    "What is this?": "¿Qué es esto?",
    "What name?...": "¿Qué nombre?...",

    // -- Compartir / SAMP / ventana ------------------------------------------
    "Connect to SAMP Hub": "Conectar al hub SAMP",
    "Contact us": "Contáctanos",
    "Documentation about Aladin Lite": "Documentación de Aladin Lite",
    "Drag the window to move it": "Arrastra la ventana para moverla",
    "Enlarge the window": "Ampliar la ventana",
    "For bug reports, discussions, feature ideas...": "Para informes de errores, debates, ideas de funciones...",
    "Full-screen": "Pantalla completa",
    "Fullscreen": "Pantalla completa",
    "General documentation": "Documentación general",
    "No hub": "Sin hub",
    "No hub?": "¿Sin hub?",
    "Oops, unable to copy": "Vaya, no se ha podido copiar",
    "Register": "Registrar",
    "SAMP disabled in Aladin Lite options": "SAMP desactivado en las opciones de Aladin Lite",
    "Send a table through SAMP Hub": "Enviar una tabla a través del hub SAMP",
    "Share view": "Compartir vista",
    "Unregister": "Anular registro",
    "Using proxy": "Usando proxy",
    "View URL saved into your clipboard!": "¡URL de la vista guardada en el portapapeles!",
    "View URL will be saved into your clipboard": "La URL de la vista se guardará en el portapapeles",
    "You can share/export your view into many ways": "Puedes compartir/exportar tu vista de muchas formas",

    // -- Regímenes de observación (filtro de sondeos) ------------------------
    "Gamma-ray": "Rayos gamma",
    "Millimeter": "Milimétrico",
    "Optical": "Óptico",
    "Radio": "Radio",
    "X-ray": "Rayos X",

    // -- Sistemas de coordenadas ------------------------------------------
    "Galactical": "Galáctica",
  };

  const ATRIBUTOS_A_TRADUCIR = ["title", "placeholder", "aria-label", "alt"];

  function traducirTexto(texto) {
    const limpio = texto.trim();
    return DICCIONARIO[limpio] || null;
  }

  function traducirNodo(nodo) {
    if (nodo.nodeType === Node.TEXT_NODE) {
      const traduccion = traducirTexto(nodo.textContent);
      if (traduccion) nodo.textContent = nodo.textContent.replace(nodo.textContent.trim(), traduccion);
      return;
    }
    if (nodo.nodeType !== Node.ELEMENT_NODE) return;

    for (const attr of ATRIBUTOS_A_TRADUCIR) {
      const valor = nodo.getAttribute && nodo.getAttribute(attr);
      if (valor) {
        const traduccion = traducirTexto(valor);
        if (traduccion) nodo.setAttribute(attr, traduccion);
      }
    }
  }

  function traducirArbol(raiz) {
    traducirNodo(raiz);
    const walker = document.createTreeWalker(raiz, NodeFilter.SHOW_ALL);
    let nodo = walker.nextNode();
    while (nodo) {
      traducirNodo(nodo);
      nodo = walker.nextNode();
    }
  }

  /**
   * Traduce el árbol del mapa ahora mismo y sigue traduciendo lo que se
   * vaya añadiendo (menús/paneles que Aladin crea solo al interactuar).
   */
  function activarTraduccionAladin(idContenedor) {
    const raiz = document.getElementById(idContenedor);
    if (!raiz) return;

    traducirArbol(raiz);

    const observer = new MutationObserver((mutaciones) => {
      for (const m of mutaciones) {
        if (m.type === "childList") {
          m.addedNodes.forEach((n) => traducirArbol(n));
        } else if (m.type === "characterData") {
          traducirNodo(m.target);
        } else if (m.type === "attributes") {
          traducirNodo(m.target);
        }
      }
    });

    observer.observe(raiz, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATRIBUTOS_A_TRADUCIR,
    });
  }

  window.activarTraduccionAladin = activarTraduccionAladin;
})();
