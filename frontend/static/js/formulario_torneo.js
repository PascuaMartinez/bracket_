/*
 * Muestra solo los campos que corresponden al formato de torneo elegido.
 *
 * Cada campo declara a qué formato pertenece con data-formato, así que
 * agregar un formato nuevo es agregar un atributo en el HTML: este
 * archivo no necesita saber cuáles existen.
 */
(function () {
  const selectorDeFormato = document.getElementById("modo");
  if (!selectorDeFormato) return;

  const camposPorFormato = document.querySelectorAll("[data-formato]");

  function actualizar() {
    const elegido = selectorDeFormato.value;

    camposPorFormato.forEach(function (campo) {
      // Un campo puede pertenecer a más de un formato.
      const corresponde = campo.dataset.formato.split(" ").includes(elegido);
      campo.hidden = !corresponde;

      /*
       * Los campos escondidos se deshabilitan además de ocultarse. Uno
       * solo oculto se sigue enviando: el backend recibiría "vidas
       * iniciales" en un torneo de eliminación. Los ignora, pero ensucia
       * lo que viaja y hace más difícil entender qué necesita cada
       * formato.
       *
       * Deshabilitar también saca el "required" de la validación del
       * navegador, que si no bloquearía el envío por un campo invisible
       * -- y quien lo usa no tendría forma de saber qué falta.
       */
      campo.querySelectorAll("input, select, textarea").forEach(function (control) {
        control.disabled = !corresponde;
      });
    });
  }

  selectorDeFormato.addEventListener("change", actualizar);

  // Al cargar también: el formulario puede volver con un formato ya
  // elegido si hubo un error de validación.
  actualizar();
})();
