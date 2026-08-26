/*
 * Reordenar la lista arrastrando.
 *
 * Se usa la API de arrastre del navegador en vez de una librería: para
 * mover elementos en una lista alcanza, y sumar una dependencia entera
 * para esto sería desproporcionado.
 */
(function () {
  const lista = document.getElementById("lista-orden");
  if (!lista) return;

  let arrastrando = null;

  lista.addEventListener("dragstart", function (evento) {
    arrastrando = evento.target.closest("[draggable]");
    if (arrastrando) arrastrando.classList.add("arrastrando");
  });

  lista.addEventListener("dragend", function () {
    if (arrastrando) arrastrando.classList.remove("arrastrando");
    arrastrando = null;
    actualizarPosiciones();
  });

  lista.addEventListener("dragover", function (evento) {
    // Sin esto el navegador no permite soltar.
    evento.preventDefault();
    if (!arrastrando) return;

    const debajo = elementoDebajoDelCursor(evento.clientY);
    if (debajo === null) {
      lista.appendChild(arrastrando);
    } else if (debajo !== arrastrando) {
      lista.insertBefore(arrastrando, debajo);
    }
  });

  /*
   * Cuál es el primer elemento cuyo centro está por debajo del cursor:
   * ahí es donde va a caer el que se arrastra.
   */
  function elementoDebajoDelCursor(y) {
    const otros = [...lista.querySelectorAll("[draggable]:not(.arrastrando)")];
    for (const elemento of otros) {
      const caja = elemento.getBoundingClientRect();
      if (y < caja.top + caja.height / 2) return elemento;
    }
    return null;
  }

  /*
   * El número visible y el campo que se envía se recalculan después de
   * cada movimiento. El orden de los campos en el formulario es el que
   * viaja al servidor, así que alcanza con que el HTML quede en orden.
   */
  function actualizarPosiciones() {
    lista.querySelectorAll("[draggable]").forEach(function (elemento, indice) {
      const numero = elemento.querySelector(".posicion");
      if (numero) numero.textContent = indice + 1;
    });
  }

  // Los botones de subir y bajar: mismo resultado que arrastrar, para
  // quien no pueda o no quiera hacerlo -- en un teléfono arrastrar es
  // incómodo, y con el teclado directamente no se puede.
  lista.addEventListener("click", function (evento) {
    const boton = evento.target.closest("[data-mover]");
    if (!boton) return;

    const fila = boton.closest("[draggable]");
    if (boton.dataset.mover === "arriba" && fila.previousElementSibling) {
      lista.insertBefore(fila, fila.previousElementSibling);
    } else if (boton.dataset.mover === "abajo" && fila.nextElementSibling) {
      lista.insertBefore(fila.nextElementSibling, fila);
    }
    actualizarPosiciones();
  });
})();
