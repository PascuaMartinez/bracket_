"""Pantallas de torneos."""
import auth
from flask import Blueprint, redirect, render_template, request, url_for

from services import api, navegacion, torneos

torneo_bp = Blueprint("torneo", __name__, url_prefix="/torneos")


@torneo_bp.route("")
def listado():
    return render_template("torneos/listado.html", torneos=torneos.listar())


@torneo_bp.route("/historial")
def historial():
    return render_template("torneos/historial.html", tabla=torneos.tabla_historica())


@torneo_bp.route("/nuevo", methods=["GET", "POST"])
@auth.requiere_sesion
def nuevo():
    jugadores = api.get("/jugadores")

    if request.method == "GET":
        # El aviso va ANTES del formulario. Dejar que alguien elija
        # jugadores, formato y fecha para rechazarlo al final es hacerle
        # perder el trabajo por una regla que se podía decir al principio.
        abierto = torneos.en_curso()
        if abierto and request.args.get("confirmado") != "si":
            return render_template("torneos/hay_uno_en_curso.html", torneo=abierto)

        return render_template("torneos/nuevo.html", jugadores=jugadores, error=None)

    datos = {
        "nombre": request.form.get("nombre"),
        "modo": request.form.get("modo"),
        "fecha": request.form.get("fecha"),
        "lugar": request.form.get("lugar"),
        "descripcion": request.form.get("descripcion"),
        # Los ids llegan como texto del formulario y el backend los espera
        # como números.
        "jugadores_ids": [int(j) for j in request.form.getlist("jugadores_ids")],
    }
    # Cada formato pide datos propios. Se mandan solo los que
    # corresponden: el backend ignora el resto, pero enviarlos igual
    # haría más difícil entender qué necesita cada uno.
    if datos["modo"] == "rey_de_la_cancha":
        datos["vidas_iniciales"] = int(request.form.get("vidas_iniciales") or 0)
    elif datos["modo"] == "grupos_eliminacion":
        datos["cantidad_grupos"] = int(request.form.get("cantidad_grupos") or 0)
        datos["cupos_eliminacion"] = int(request.form.get("cupos_eliminacion") or 0)

    try:
        creado = torneos.crear(datos)
    except api.ErrorDeApi as e:
        # Se vuelve al formulario con el motivo: el backend ya explica por
        # qué no se pudo, así que repetir esa validación acá sería tener la
        # misma regla escrita en dos lugares.
        return render_template("torneos/nuevo.html", jugadores=jugadores,
                               error=str(e), form=request.form), 400

    return redirect(url_for("torneo.detalle", torneo_id=creado["id"]))


@torneo_bp.route("/<int:torneo_id>")
def detalle(torneo_id):
    datos = torneos.detalle_completo(torneo_id)
    # Los grupos solo existen en un formato: se piden aparte y solo
    # cuando corresponde, en vez de que todos los torneos paguen una
    # llamada que casi siempre viene vacía.
    if datos["torneo"]["modo"] == "grupos_eliminacion":
        datos["grupos"] = torneos.grupos(torneo_id)

        # Si quedó algo sin resolver, se trae cómo le fue a cada uno en su
        # grupo: son de grupos distintos y pueden haber llegado ahí de
        # formas muy diferentes, así que decidir a ciegas sería peor.
        sin_resolver = [f["jugador_id"] for g in datos["grupos"]
                        for f in g["tabla"] if f.get("sin_resolver")]
        if sin_resolver:
            datos["desempeno"] = api.get(
                f"/torneos/{torneo_id}/desempeno", jugadores=sin_resolver
            )

    # Los torneos vienen del más nuevo al más viejo, así que "siguiente"
    # lleva a uno más viejo. Se invierten para que la flecha derecha
    # avance en el tiempo, que es lo que uno espera al recorrerlos.
    datos["estadisticas"] = api.get(f"/torneos/{torneo_id}/estadisticas")

    anterior, siguiente = navegacion.vecinos(torneos.listar(), torneo_id)
    datos["anterior"], datos["siguiente"] = siguiente, anterior

    return render_template("torneos/detalle.html", **datos)


@torneo_bp.route("/<int:torneo_id>/jugar", methods=["GET", "POST"])
@auth.requiere_sesion
def jugar(torneo_id):
    """La pantalla que se usa durante el torneo: muestra el partido en
    curso y recibe el resultado."""
    if request.method == "POST":
        torneos.cargar_resultado(
            int(request.form["partido_id"]),
            {
                "ganador_id": int(request.form["ganador_id"]),
                "peleador1_id": _entero_o_nada(request.form.get("peleador1_id")),
                "peleador2_id": _entero_o_nada(request.form.get("peleador2_id")),
                "rondas_jugadas": _entero_o_nada(request.form.get("rondas_jugadas")),
            },
        )
        # Redirigir después de guardar evita que recargar la página vuelva
        # a enviar el mismo resultado.
        return redirect(url_for("torneo.jugar", torneo_id=torneo_id))

    partido = torneos.partido_actual(torneo_id)
    if partido is None:
        return redirect(url_for("torneo.detalle", torneo_id=torneo_id))

    # Los pospuestos se muestran junto al partido actual: si quedaron
    # afuera de la vista, es fácil terminar el torneo sin acordarse de
    # que faltaban jugar.
    lista_pospuestos = torneos.pospuestos(torneo_id)

    # Se traen todos, incluidos los ocultos: un torneo viejo puede tener
    # un partido pendiente de alguien que después se sacó del sistema, y
    # la pantalla necesita poder nombrarlo.
    jugadores = {j["id"]: j for j in api.get("/jugadores", incluir_ocultos="si")}
    nombres = {jid: j["nombre"] for jid, j in jugadores.items()}

    return render_template(
        "torneos/jugar.html",
        jugador1=jugadores.get(partido["jugador1_id"], {}),
        jugador2=jugadores.get(partido["jugador2_id"], {}),
        torneo=torneos.obtener(torneo_id),
        partido=partido,
        nombre1=nombres.get(partido["jugador1_id"]),
        nombre2=nombres.get(partido["jugador2_id"]),
        peleadores=api.get("/peleadores"),
        pospuestos=lista_pospuestos,
        nombres=nombres,
    )


def _entero_o_nada(valor):
    """Los campos opcionales llegan como texto vacío cuando no se
    completan, y el backend espera un número o nada."""
    return int(valor) if valor else None


@torneo_bp.route("/<int:torneo_id>/editar", methods=["GET", "POST"])
@auth.requiere_sesion
def editar(torneo_id):
    """
    Solo se editan los datos descriptivos: nombre, fecha, lugar y
    descripción.

    El formato y los participantes NO se pueden cambiar. Con partidos ya
    jugados, cambiar el formato dejaría el torneo inconsistente con lo que
    efectivamente pasó, y sacar a alguien que ya jugó dejaría resultados
    huérfanos. Si hay que corregir eso, corresponde borrar el torneo y
    rehacerlo.
    """
    if request.method == "GET":
        return render_template("torneos/editar.html",
                               torneo=torneos.obtener(torneo_id), error=None)

    try:
        torneos.actualizar(torneo_id, {
            "nombre": request.form.get("nombre"),
            "fecha": request.form.get("fecha"),
            "lugar": request.form.get("lugar"),
            "descripcion": request.form.get("descripcion"),
        })
    except api.ErrorDeApi as e:
        return render_template("torneos/editar.html", torneo=request.form,
                               error=str(e)), 400

    return redirect(url_for("torneo.detalle", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/eliminar", methods=["POST"])
@auth.requiere_sesion
def eliminar(torneo_id):
    torneos.eliminar(torneo_id)
    return redirect(url_for("torneo.listado"))


@torneo_bp.route("/<int:torneo_id>/partidos/<int:partido_id>/posponer", methods=["POST"])
@auth.requiere_sesion
def posponer(torneo_id, partido_id):
    torneos.posponer(partido_id)
    return redirect(url_for("torneo.jugar", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/partidos/<int:partido_id>/retomar", methods=["POST"])
@auth.requiere_sesion
def retomar(torneo_id, partido_id):
    torneos.retomar(partido_id)
    return redirect(url_for("torneo.jugar", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/grupos/<int:grupo_id>/resolver", methods=["POST"])
@auth.requiere_sesion
def resolver_empate(torneo_id, grupo_id):
    torneos.resolver_empate(
        torneo_id, grupo_id,
        int(request.form["jugador_id"]),
        request.form.get("clasifica") == "si",
        request.form.get("observacion") or None,
    )
    return redirect(url_for("torneo.detalle", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/corregir", methods=["GET", "POST"])
@auth.requiere_sesion
def corregir(torneo_id):
    """
    Corregir un resultado ya cargado.

    Sirve para el error de carga: se tocó el nombre equivocado o se
    registró mal el personaje. Sin esto, ese error quedaría para siempre
    en las estadísticas.
    """
    jugadores = {j["id"]: j for j in api.get("/jugadores", incluir_ocultos="si")}

    if request.method == "POST":
        try:
            torneos.corregir_resultado(int(request.form["partido_id"]), {
                "ganador_id": int(request.form["ganador_id"]),
                "peleador1_id": _entero_o_nada(request.form.get("peleador1_id")),
                "peleador2_id": _entero_o_nada(request.form.get("peleador2_id")),
                "rondas_jugadas": _entero_o_nada(request.form.get("rondas_jugadas")),
            })
        except api.ErrorDeApi as e:
            return render_template(
                "torneos/corregir.html", torneo=torneos.obtener(torneo_id),
                partidos=torneos.corregibles(torneo_id), jugadores=jugadores,
                peleadores=api.get("/peleadores"), error=str(e),
            ), 400

        return redirect(url_for("torneo.detalle", torneo_id=torneo_id))

    return render_template(
        "torneos/corregir.html",
        torneo=torneos.obtener(torneo_id),
        partidos=torneos.corregibles(torneo_id),
        jugadores=jugadores,
        peleadores=api.get("/peleadores"),
        error=None,
    )


@torneo_bp.route("/<int:torneo_id>/reordenar", methods=["GET", "POST"])
@auth.requiere_sesion
def reordenar(torneo_id):
    """
    Reordenar los cruces del cuadro antes de que arranque.

    La siembra automática ordena por nivel, que es lo correcto en general.
    Pero quien organiza a veces sabe cosas que el sistema no: que dos
    vinieron juntos y preferirían no cruzarse de entrada, que alguien se
    tiene que ir temprano.
    """
    if request.method == "POST":
        try:
            torneos.resembrar(
                torneo_id,
                [int(j) for j in request.form.getlist("jugadores_ids")],
            )
        except api.ErrorDeApi as e:
            return render_template(
                "torneos/reordenar.html", torneo=torneos.obtener(torneo_id),
                cruces=_cruces_actuales(torneo_id), error=str(e),
            ), 400

        return redirect(url_for("torneo.detalle", torneo_id=torneo_id))

    return render_template(
        "torneos/reordenar.html",
        torneo=torneos.obtener(torneo_id),
        cruces=_cruces_actuales(torneo_id),
        error=None,
    )


def _cruces_actuales(torneo_id):
    """
    Los jugadores del cuadro en el orden de siembra actual.

    Se reconstruye desde los partidos y no se guarda aparte: el cuadro ya
    es la fuente de verdad del orden, y tener una segunda copia sería otra
    cosa que puede desincronizarse.
    """
    jugadores = {j["id"]: j for j in api.get("/jugadores", incluir_ocultos="si")}
    partidos = [p for p in api.get(f"/torneos/{torneo_id}/partidos")
                if p.get("ronda") == 1]
    partidos.sort(key=lambda p: p.get("orden") or 0)

    # La siembra enfrenta al primero con el último: para recuperar el
    # orden original se leen los de arriba hacia abajo y los de abajo en
    # sentido inverso.
    arriba = [p["jugador1_id"] for p in partidos]
    abajo = [p["jugador2_id"] for p in reversed(partidos) if p["jugador2_id"]]

    return [jugadores.get(jid, {"id": jid, "nombre": "?"}) for jid in arriba + abajo]


@torneo_bp.route("/<int:torneo_id>/repetir-desempate", methods=["POST"])
@auth.requiere_sesion
def repetir_desempate(torneo_id):
    torneos.repetir_desempate(
        torneo_id, [int(j) for j in request.form.getlist("jugadores_ids")]
    )
    return redirect(url_for("torneo.detalle", torneo_id=torneo_id))


@torneo_bp.route("/descartar-en-curso", methods=["POST"])
@auth.requiere_sesion
def descartar_en_curso():
    """
    Borra el torneo abierto para poder crear otro.

    Es destructivo a propósito y no hay alternativa suave: dar por
    finalizado un torneo a medio jugar sería peor. Sus partidos
    incompletos entrarían al historial como si fueran un torneo real, con
    jugadores que jugaron cinco partidos y otros que jugaron dos, y esa
    distorsión se propagaría a la tabla histórica y a los ratings.
    """
    torneos.eliminar(int(request.form["torneo_id"]))
    return redirect(url_for("torneo.nuevo", confirmado="si"))
