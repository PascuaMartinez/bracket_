/*
 * Armado manual del torneo.
 *
 * Según el formato, permite ordenar a los jugadores o asignarlos a
 * grupos. Los controles se llenan con los que están tildados y solo
 * aparecen si se pidió armar a mano: en el caso normal el formulario
 * queda igual que antes.
 */
(function () {
  const selectorDeFormato = document.getElementById("modo");
  const casilla = document.getElementById("armado_manual");
  const panel = document.getElementById("panel-manual");
  if (!selectorDeFormato || !casilla || !panel) return;

  const panelOrden = document.getElementById("panel-orden");
  const panelGrupos = document.getElementById("panel-grupos");
  const listaOrden = document.getElementById("lista-orden-nuevo");
  const listaGrupos = document.getElementById("lista-grupos");
  const vistaCruces = document.getElementById("vista-cruces");
  const avisoGrupos = document.getElementById("aviso-grupos");
  const etiqueta = document.getElementById("etiqueta-armado-manual");
  const ayudaManual = document.getElementById("ayuda-armado-manual");
  const ayudaOrden = document.getElementById("ayuda-orden");

  // Qué significa "a mano" en cada formato: no es lo mismo ordenar una
  // cola que repartir grupos.
  const TEXTOS = {
    eliminacion: {
      etiqueta: "Armar las llaves a mano",
      ayuda: "Si no, se siembra por nivel: el primero contra el último.",
      orden: "El orden define los cruces. Arrastrá o usá las flechas.",
    },
    rey_de_la_cancha: {
      etiqueta: "Elegir el orden de la cola a mano",
      ayuda: "Si no, entran en el orden en que aparecen listados.",
      orden: "Los dos primeros juegan el primer partido; el resto espera en ese orden.",
    },
    grupos_eliminacion: {
      etiqueta: "Armar los grupos a mano",
      ayuda: "Si no, se reparten en zigzag para que queden equilibrados.",
      orden: "",
    },
  };

  function jugadoresElegidos() {
    return [...document.querySelectorAll('input[name="jugadores_ids"]:checked')].map(
      function (control) {
        const etiquetaDelJugador = control.closest("label");
        return {
          id: control.value,
          nombre: etiquetaDelJugador ? etiquetaDelJugador.textContent.trim() : control.value,
        };
      }
    );
  }

  function actualizar() {
    const formato = selectorDeFormato.value;
    const textos = TEXTOS[formato];

    if (!textos) {
      panel.hidden = true;
      return;
    }

    etiqueta.textContent = textos.etiqueta;
    ayudaManual.textContent = textos.ayuda;

    panel.hidden = !casilla.checked;
    if (!casilla.checked) {
      // Los controles escondidos se vacían: si quedaran cargados,
      // seguirían enviando datos de un armado que ya no se pidió.
      listaOrden.innerHTML = "";
      listaGrupos.innerHTML = "";
      return;
    }

    const jugadores = jugadoresElegidos();
    const esPorGrupos = formato === "grupos_eliminacion";

    panelOrden.hidden = esPorGrupos;
    panelGrupos.hidden = !esPorGrupos;

    if (esPorGrupos) {
      dibujarGrupos(jugadores);
    } else {
      ayudaOrden.textContent = textos.orden;
      dibujarOrden(jugadores, formato === "eliminacion");
    }
  }

  function dibujarOrden(jugadores, mostrarCruces) {
    listaOrden.innerHTML = "";
    jugadores.forEach(function (jugador, indice) {
      const fila = document.createElement("li");
      fila.className = "fila-ordenable";
      fila.draggable = true;
      fila.innerHTML =
        '<span class="posicion">' + (indice + 1) + "</span>" +
        '<span class="nombre-ordenable"></span>' +
        '<span class="botones-mover">' +
        '<button type="button" class="enlace-boton" data-mover="arriba">↑</button>' +
        '<button type="button" class="enlace-boton" data-mover="abajo">↓</button>' +
        "</span>" +
        '<input type="hidden" name="orden_jugadores" value="' + jugador.id + '">';
      // El nombre se asigna como texto y no como HTML: viene de un dato
      // cargado por el usuario y podría contener etiquetas.
      fila.querySelector(".nombre-ordenable").textContent = jugador.nombre;
      listaOrden.appendChild(fila);
    });

    vistaCruces.hidden = !mostrarCruces;
    if (mostrarCruces) dibujarCruces();
  }

  /*
   * Los cruces que salen del orden actual: primero contra último,
   * segundo contra anteúltimo. Se muestran para no tener que
   * imaginarlos, que es lo que hace difícil ordenar un cuadro.
   */
  function dibujarCruces() {
    const nombres = [...listaOrden.querySelectorAll(".nombre-ordenable")].map(
      (elemento) => elemento.textContent
    );

    const partes = [];
    for (let i = 0; i < Math.floor(nombres.length / 2); i++) {
      partes.push(nombres[i] + " vs " + nombres[nombres.length - 1 - i]);
    }
    // Con cantidad impar, el del medio pasa libre.
    if (nombres.length % 2 === 1) {
      partes.push(nombres[Math.floor(nombres.length / 2)] + " pasa libre");
    }

    vistaCruces.innerHTML = "<p class='ayuda'>Primera ronda</p>";
    partes.forEach(function (texto) {
      const linea = document.createElement("p");
      linea.className = "cruce";
      linea.textContent = texto;
      vistaCruces.appendChild(linea);
    });
  }

  function cantidadDeGrupos() {
    const control = document.getElementById("cantidad_grupos");
    return Math.max(2, parseInt(control && control.value, 10) || 2);
  }

  function dibujarGrupos(jugadores) {
    const grupos = cantidadDeGrupos();
    listaGrupos.innerHTML = "";

    jugadores.forEach(function (jugador, indice) {
      const fila = document.createElement("div");
      fila.className = "fila-grupo";

      const nombre = document.createElement("span");
      nombre.className = "nombre-ordenable";
      nombre.textContent = jugador.nombre;

      const selector = document.createElement("select");
      selector.name = "grupo_de_" + jugador.id;
      for (let i = 0; i < grupos; i++) {
        const opcion = document.createElement("option");
        opcion.value = i;
        opcion.textContent = "Grupo " + String.fromCharCode(65 + i);
        // Se reparte en zigzag como sugerencia inicial: es un punto de
        // partida válido que ya cumple la regla de paridad.
        if (i === indice % grupos) opcion.selected = true;
        selector.appendChild(opcion);
      }
      selector.addEventListener("change", revisarParidad);

      fila.appendChild(nombre);
      fila.appendChild(selector);
      listaGrupos.appendChild(fila);
    });

    revisarParidad();
  }

  /*
   * Avisa si los grupos quedaron desparejos.
   *
   * El backend lo rechaza igual, pero enterarse al apretar crear es
   * tarde: acá se ve mientras se arma.
   */
  function revisarParidad() {
    const conteo = {};
    listaGrupos.querySelectorAll("select").forEach(function (selector) {
      conteo[selector.value] = (conteo[selector.value] || 0) + 1;
    });

    const cantidades = Object.values(conteo);
    const grupos = cantidadDeGrupos();
    const vacios = grupos - cantidades.length;

    if (vacios > 0) {
      avisoGrupos.textContent = "Hay " + vacios + " grupo(s) sin nadie asignado.";
      return;
    }

    const diferencia = Math.max(...cantidades) - Math.min(...cantidades);
    avisoGrupos.textContent =
      diferencia > 1
        ? "Los grupos quedaron desparejos: hay uno de " + Math.max(...cantidades) +
          " y otro de " + Math.min(...cantidades) + "."
        : "";
  }

  selectorDeFormato.addEventListener("change", actualizar);
  casilla.addEventListener("change", actualizar);
  document.addEventListener("change", function (evento) {
    // La lista de jugadores cambia lo que hay que ordenar o repartir.
    if (evento.target.name === "jugadores_ids" || evento.target.id === "cantidad_grupos") {
      actualizar();
    }
  });

  // Reordenar arrastrando, igual que en la pantalla de reordenar cuadro.
  let arrastrando = null;
  listaOrden.addEventListener("dragstart", function (evento) {
    arrastrando = evento.target.closest("[draggable]");
    if (arrastrando) arrastrando.classList.add("arrastrando");
  });
  listaOrden.addEventListener("dragend", function () {
    if (arrastrando) arrastrando.classList.remove("arrastrando");
    arrastrando = null;
    renumerar();
  });
  listaOrden.addEventListener("dragover", function (evento) {
    evento.preventDefault();
    if (!arrastrando) return;
    const debajo = [...listaOrden.querySelectorAll("[draggable]:not(.arrastrando)")].find(
      function (elemento) {
        const caja = elemento.getBoundingClientRect();
        return evento.clientY < caja.top + caja.height / 2;
      }
    );
    if (debajo) listaOrden.insertBefore(arrastrando, debajo);
    else listaOrden.appendChild(arrastrando);
  });

  listaOrden.addEventListener("click", function (evento) {
    const boton = evento.target.closest("[data-mover]");
    if (!boton) return;
    const fila = boton.closest("[draggable]");
    if (boton.dataset.mover === "arriba" && fila.previousElementSibling) {
      listaOrden.insertBefore(fila, fila.previousElementSibling);
    } else if (boton.dataset.mover === "abajo" && fila.nextElementSibling) {
      listaOrden.insertBefore(fila.nextElementSibling, fila);
    }
    renumerar();
  });

  function renumerar() {
    listaOrden.querySelectorAll("[draggable]").forEach(function (fila, indice) {
      fila.querySelector(".posicion").textContent = indice + 1;
    });
    if (!vistaCruces.hidden) dibujarCruces();
  }

  actualizar();
})();
