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

/*
 * Sugerencia de cuántos clasifican.
 *
 * Un cuadro de eliminación funciona mejor con una potencia de dos: 4 son
 * semifinales, 8 cuartos. Con otra cantidad hay pases libres, que le dan
 * ventaja a algunos sin haberla ganado.
 *
 * Se sugiere, no se impone: quien organiza puede tener motivos para
 * elegir otra cosa.
 */
(function () {
  const cupos = document.getElementById("cupos_eliminacion");
  const aviso = document.getElementById("sugerencia-cupos");
  if (!cupos || !aviso) return;

  function jugadoresElegidos() {
    return document.querySelectorAll('input[name="jugadores_ids"]:checked').length;
  }

  function sugerir() {
    const cantidad = jugadoresElegidos();
    if (cantidad < 4) {
      aviso.textContent = "";
      return;
    }

    // La misma regla que el backend: la potencia de dos más grande que
    // deje afuera al menos a un tercio.
    const limite = (cantidad * 2) / 3;
    let potencia = 2;
    while (potencia * 2 < limite) potencia *= 2;

    const nombre = { 2: "la final", 4: "semifinales", 8: "cuartos de final" };
    const instancia = nombre[potencia] || `una ronda de ${potencia}`;
    aviso.textContent =
      `Con ${cantidad} jugadores, ${potencia} clasificados arrancan en ${instancia}.`;
  }

  document.addEventListener("change", function (evento) {
    if (evento.target.name === "jugadores_ids") sugerir();
  });

  sugerir();
})();
